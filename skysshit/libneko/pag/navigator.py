#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# MIT License
#
# Copyright (c) 2018-2019 Flitt3r (a.k.a Koyagami)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in a$
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


__all__ = (
    "PageT",
    "ChannelT",
    "CancelAction",
    "CancelIteration",
    "FakeContext",
    "BaseNavigator",
    "StringNavigator",
    "EmbedNavigator",
)

import asyncio
import collections
import enum
import sys
from abc import abstractmethod
from typing import Generic, Sequence, TypeVar, Union, Optional, TYPE_CHECKING, Iterator

import async_timeout
import discord
from discord.ext import commands

from libneko import logging
from . import abc

# Stops looped lookups failing.
if TYPE_CHECKING:
    from .reactionbuttons import Button

PageT = TypeVar("PageT")

ChannelT = Union[discord.TextChannel, discord.DMChannel]

_logger = logging.get_logger("libneko.pag.navigator")


class _Flag:
    """Settable/unsettable flag."""

    __slots__ = ("value",)

    def __init__(self, value: bool):
        self.value = value

    def set(self):
        """Sets the flag."""
        self.value = True

    def reset(self):
        """Unsets the flag."""
        self.value = False

    def __bool__(self):
        return self.value


class CancelAction(enum.IntFlag):
    """
    Represents a cleanup action to perform on the navigator terminating.

    These are bitwise flags. To represent multiple actions, simply
    bitwise-or them together::

        # Will remove the paginator reactions and the message that
        # initially lead to the navigator being displayed.
        action = CancelAction.REMOVE_REACTS | CancelAction.REMOVE_INVOCATION

    """

    DO_NOTHING = 0x0
    REMOVE_REACTS = 0x1
    REMOVE_NON_ROOT_MESSAGES = 0x2
    REMOVE_ROOT_MESSAGE = 0x4
    REMOVE_INVOCATION = 0x8

    REMOVE_ALL_SENT_MESSAGES = REMOVE_NON_ROOT_MESSAGES | REMOVE_ROOT_MESSAGE
    REMOVE_ALL_MESSAGES = REMOVE_ALL_SENT_MESSAGES | REMOVE_INVOCATION


class CancelIteration(Exception):
    """
    Raised to signal the navigator should terminate.

    Takes a combination of ``CancelAction`` flags as the sole argument
    to specify a custom cleanup action to perform.
    """

    __slots__ = ("requested_behaviour",)

    def __init__(self, requested_behaviour: Union[int, CancelAction]):
        """
        Init the exception.

        Args:
            requested_behaviour:
                Requested behaviour regarding how to tidy up messages on exit.
        """
        self.requested_behaviour = requested_behaviour


class FakeContext:
    """
    Context-compatible object that only stores the info we need
    internally.

    This is a monkeypatch-style class compatible with the
    ``discord.ext.commands.Context`` class that can be used in-place
    if you are showing a paginator in a situation where a proper
    ``discord.ext.commands.Context`` would normally be.

    Note:
        As with the old "discomaton" paginator, you can also just
        provide a tuple of ``(discord.User, discord.Message, discord.Client)``
        covariants.
    """

    __bases__ = commands.Context

    __slots__ = "author", "message", "bot"

    def __init__(self, author: discord.User, message: discord.Message, bot: discord.Client):
        #: The message author.
        self.author = author
        #: Message object.
        self.message = message
        #: Global bot object.
        self.bot = bot

    @property
    def client(self):
        """Returns the bot object."""
        return self.bot

    @property
    def guild(self) -> Optional[discord.Guild]:
        """The guild, or None if a DM."""
        return self.message.guild

    @property
    def channel(self) -> ChannelT:
        """The channel."""
        return self.message.channel


class BaseNavigator(abc.PagABC, Generic[PageT]):
    """
    Navigation for a set of pages, given a set of button objects to display as reactions.

    Implementation that takes a collection of string chunks, sending the first to
    a given channel. It then displays a set of reactions on the message that when
    the user interacts with them, it will change the content of the message.

    This emulates an interface that allows "turning of pages" by adding discord
    reactions to the message.


    Args:
        ctx:
            the command context to invoke in response to. If you are using this in
            an event listener, you can generate a ``FakeContext`` to go in here.
        pages:
            A sequence of elements to display.
        buttons:
            A sequence of ``Button`` objects.

    Keyword Args:
        timeout:
            An integer or floating point positive number representing the number of seconds
            to be inactive for before destroying this navigation session. Defaults to 300s
            (5 minutes).
        initial_page:
            The initial page index to start on. Defaults to 0.

    Attributes:
        owner:
            The original user who invoked the event leading to this navigator being displayed.
            Change this to alter who has control over the navigator. Set to None to unlock the
            navigator to all users for control.
        channel:
            The channel we are responding in.
        bot:
            The bot that is sending this paginator. Can be anything derived from discord.Client.
        pages:
            The sequence of pages to display from.
        buttons:
            The ordered mapping of emoji to button for reactions to display.
        timeout:
            The inactive timeout period.
        invoked_by:
            The original invoking message.

    Note:
        Buttons can take control of most parts of this object. To kill the pagination
        early, one should raise a ``CancelIteration`` from the button logic. This exception
        can take an argument that consists of a combination of one or more ``CancelAction``
        enumerations combined via bitwise-or. These flags allow custom specification of what
        to do on cleaning up (e.g. should we delete the root message, or just clear the reactions?)

    Note:
        The formatting for the page number can be overridden easily, or disabled, if you prefer.
        To disable the formatting altogether, you can override the format_page_number method to
        return an empty string. This can be achieved by subclassing the navigator you are using...
        or just monkey-patching the
        method when needed::

            >>> nav = StringNavigator()

            >>> # Notice the lack of a `self' parameter!!
            >>> nav.format_page_number = lambda: ''

    """

    def __init__(
        self,
        ctx: Union[commands.Context, FakeContext, tuple],
        pages: Sequence[PageT],
        buttons: Sequence["Button"] = None,
        *,
        timeout: float = 300,
        initial_page: int = 0,
    ):
        from libneko.pag.reactionbuttons import Button

        if isinstance(ctx, tuple):
            ctx = FakeContext(*ctx)

        if buttons is None:
            from .reactionbuttons import default_buttons

            buttons = default_buttons()

        buttons = [isinstance(b, Button) and b or b() for b in buttons]

        if timeout is None:
            raise TypeError("Expected int or float, not NoneType.")
        elif timeout <= 0:
            raise ValueError("Cannot have a non-positive timeout.")
        else:
            #: Ready event.
            self.is_ready = asyncio.Event(loop=ctx.bot.loop)
            #: Finished event.
            self.is_finished = asyncio.Event(loop=ctx.bot.loop)
            self._event_queue = asyncio.Queue(loop=ctx.bot.loop)
            # Messages sent by this navigator. The first in this list is considered
            # to be the root message.
            self._messages = []
            # Flag set internally if anything is altered. Saves bandwidth for
            # otherwise pointless operations.
            self._should_refresh = _Flag(False)

            #: Owner of the navigator.
            self.owner = ctx.author
            #: Channel the navigator is showing in.
            self.channel = ctx.channel
            #: Bot object of the navigator (holds the event loop and wait_for methods).
            self.bot = ctx.bot
            #: List of objects to display.
            self.pages = pages

            self._page_index = 0
            #: Current page index.
            self.page_index = initial_page

            # Register ownership.
            for button in buttons:
                button.owner = self

            #: Any buttons to show on the navigator.
            self.buttons = collections.OrderedDict((btn.emoji, btn) for btn in buttons)

            #: Idle time to wait for before destroying the navigator.
            self.timeout = timeout

            #: Message that triggered this navigator to be created.
            self.invoked_by = ctx.message

            super().__init__()

    def create_task(self, coro):
        """Creates a task and mutes any errors to single lines."""
        t = self.loop.create_task(coro)

        @t.add_done_callback
        def on_done(error):
            try:
                t.result()
            except Exception as ex:
                _logger.exception(f"{coro} task raised {type(ex).__name__} {ex} because of {error}")

        return t

    @property
    def loop(self):
        """The main event loop the bot is running."""
        return self.bot.loop

    def __await__(self):
        """Await the completion of the Navigator."""
        return self.is_finished.wait()

    def __len__(self):
        return len(self.pages)

    def __repr__(self):
        return f"<{type(self).__name__} " + " ".join(
            k + "=" + repr(getattr(self, k)) for k in dir(self)
        )

    __str__ = __repr__

    def memory_usage(self) -> int:
        """Gets the rough number of bytes being used to store the pages in memory."""
        return sum(sys.getsizeof(p, 0) for p in self.pages)

    @property
    def root_message(self):
        """The root message. This is only used internally and by derived implementations."""
        return self._messages[0]

    async def send(self, *args, add_to_list=True, **kwargs):
        """|coro|

        Internal helper for sending messages.

        Any messages sent via this interface will be added to the
        message stack internally and cleaned up when the booklet gets
        destroyed.

        Args, Kwargs, amd return value:
            See ``discord.Messageable.send``.

        """
        m = await self.channel.send(*args, **kwargs)

        if add_to_list:
            self._messages.append(m)

        return m

    @root_message.setter
    def root_message(self, message):
        """The first and main message holding the page content."""
        if not self._messages:
            self._messages = [message]
        else:
            self._messages[0] = message

    @property
    def additional_messages(self) -> Iterator[discord.Message]:
        """Yield any additional messages (if any exist) linked to this nav."""
        yield from self._messages[1:]

    @property
    def all_messages(self) -> Iterator[discord.Message]:
        """Yield all messages linked to this nav."""
        yield from self._messages

    @property
    def current_page(self) -> PageT:
        """Gets the current page that should be being displayed."""
        return self.pages[self.page_index]

    @property
    def page_index(self):
        """Gets/sets the page index (0-based)."""
        return self._page_index

    @page_index.setter
    def page_index(self, index):
        size = len(self)

        if size > 0:
            while index < 0:
                index += size

            while index and index >= size:
                index -= size

            if index != self.page_index:
                self._should_refresh.set()

            self._page_index = index
        else:
            self.index = 0

    @property
    def page_number(self):
        """Gets/sets the page number (1-based, does not support out of range)."""
        return self.page_index + 1

    @page_number.setter
    def page_number(self, number):
        if 1 <= number <= len(self):
            self.page_index = number - 1
        else:
            raise ValueError("Invalid page number")

    def lock(self):
        """Reset the owner of the control."""
        self.owner = self.invoked_by.author

    def unlock(self):
        """Allow anyone to use the control."""
        self.owner = None

    async def _on_reaction_add(self, reaction, user):
        """|coro|

        Sends a reaction addition event.
        """

        if self.is_ready.is_set() and self._messages:
            if reaction.message.id != self.root_message.id:
                return

            # Update our state!
            self.root_message = reaction.message

            not_me = user != self.bot.user

            valid_button = reaction.emoji in self.buttons

            is_in_whitelist = (
                self.owner is None or user == self.owner or user == self.invoked_by.author
            )

            if not_me and valid_button and is_in_whitelist:
                await self._event_queue.put((reaction, user))

    # @print_result
    async def _on_message_delete(self, message):
        """|coro|

        Sends a message deletion event for any message we made in this navigator.
        """
        if self._messages and self._messages[0].id == message.id:
            try:
                self.__task.cancel()
            except AttributeError:
                # Depending how quickly discord redispatches the event
                # to say the message was deleted, our task may or may not
                # already have been destroyed. If it has been, then just
                # ignore the attribute error.
                pass

        if self.is_ready.is_set():
            message = discord.utils.get(self._messages, id=message.id)
            if message is not None:
                self._messages.remove(message)

    async def _handle_reaction(self, reaction, user):
        """|coro|

        Dispatches a reaction.
        """
        emoji = reaction.emoji
        # noinspection PyUnresolvedReferences
        await self.buttons[emoji].invoke(reaction, user)

    @abstractmethod
    async def _edit_page(self):
        """|coro|

        Logic for changing whatever is on Discord to display the correct value.
        """
        ...

    def format_page_number(self) -> str:
        """Formats the page number."""
        return f"[{self.page_number}/{len(self)}]\n"

    def start(self):
        """
        Returns an ensured task that can be optionally awaited.
        """
        # noinspection PyAttributeOutsideInit
        self.__task = self.loop.create_task(self._run())

        @self.__task.add_done_callback
        def on_done(_):
            try:
                self.__task.result()
            except AttributeError:
                # Task was already destroyed. We can't do anything else.
                pass
            except asyncio.CancelledError:
                # Task was cancelled. That is fine. No need to report an error.
                pass
            except Exception:
                _logger.exception(
                    f"Exception occurred in {type(self).__name__}.start()", exc_info=True
                )
            finally:
                try:
                    del self.__task
                finally:
                    return

        return self.__task

    def kill(self, action: CancelAction = CancelAction.REMOVE_ALL_MESSAGES):
        """
        Stops the loop if it is running.

        Parameters:
            action:
                The action to take to clean up.
        """
        if self.__task:
            try:
                setattr(self, "_force_kill_reason", CancelIteration(action))
                self.__task.cancel()
            except Exception:
                pass

    async def _run(self):
        """|coro|

        Runs the main logic loop for the navigator.
        """
        if not self.pages or not all(self.pages):
            raise ValueError("Empty pages exist.")

        if self.is_ready.is_set():
            raise RuntimeError("Already running this navigator.")

        self.bot.listen("on_message_delete")(self._on_message_delete)
        self.bot.listen("on_reaction_add")(self._on_reaction_add)

        try:

            async def produce_page():
                # Initialise the first page.
                self.root_message = await self.send("Loading...")
                self.create_task(self._edit_page())
                return self.root_message

            await produce_page()

            self.is_finished.clear()
            self.is_ready.set()

            while True:
                # Ensure the reactions are all correct. If they are not, then
                # attempt to adjust them.
                try:
                    # Refresh the root message state
                    # self.__root = await self.channel.fetch_message(self.__root.id)
                    try:
                        root = self.root_message
                    except IndexError:
                        root = await produce_page()

                    current_reacts = root.reactions
                    expected_reacts = [
                        b.emoji for b in self.buttons.values() if await b.should_show()
                    ]

                    for react in current_reacts:
                        # If the current react doesn't match the one at the list head,
                        # then we assume it should not be here, so we remove it. If we
                        # have got to the end of our targets list, we assume everything
                        # else is garbage, and thus we delete it.
                        if not expected_reacts or react.emoji != expected_reacts[0]:
                            async for user in react.users():
                                self.create_task(root.remove_reaction(react, user))

                        # If there are still targets left to check and the current
                        # reaction is the next target, remove all reacts that are not by
                        # me.
                        elif react.emoji == expected_reacts[0]:
                            expected_reacts.pop(0)
                            async for user in react.users():
                                # Ignore our own react. We want to keep that.
                                if user != self.bot.user:
                                    self.create_task(root.remove_reaction(react, user))

                except discord.Forbidden:
                    # If we can't update them, just continue.
                    await self._permission_error()
                else:
                    # If we did not validate all targets by now, we know they are
                    # missing and should be added
                    if expected_reacts:
                        try:
                            for r in expected_reacts:
                                await self.root_message.add_reaction(r)
                        except discord.Forbidden:
                            await self._permission_error()
                        except discord.NotFound:
                            raise CancelIteration(CancelAction.REMOVE_NON_ROOT_MESSAGES)
                # Get next event, or wait.
                # This is essentially a polling pipe between the event captures
                # and the handlers. I could have used wait_for, but that encouraged
                # spaghetti code in the old paginator. This is more modular and
                # easy to understand.
                # This is required to enable us to intercept signals sent via
                # exceptions.
                with async_timeout.timeout(self.timeout):
                    reaction, user = await self._event_queue.get()
                    await self._handle_reaction(reaction, user)

                if self._should_refresh:
                    self.create_task(self._edit_page())
                    self._should_refresh.reset()

        except (
            asyncio.TimeoutError,
            asyncio.CancelledError,
            discord.NotFound,
            CancelIteration,
        ) as ex:
            # Request to shut down the navigator.

            if hasattr(self, "_force_kill_reason"):
                ex = getattr(self, "_force_kill_reason")

            r = (
                ex.requested_behaviour
                if isinstance(ex, CancelIteration)
                else CancelAction.REMOVE_NON_ROOT_MESSAGES | CancelAction.REMOVE_REACTS
            )

            if r & CancelAction.REMOVE_ROOT_MESSAGE:
                try:
                    await self.root_message.delete()
                except (discord.NotFound, discord.Forbidden, IndexError, ValueError):
                    pass

            elif r & CancelAction.REMOVE_REACTS:
                try:
                    await self.root_message.clear_reactions()
                except (discord.NotFound, discord.Forbidden, IndexError, ValueError):
                    pass

            if r & CancelAction.REMOVE_NON_ROOT_MESSAGES:
                try:
                    await asyncio.gather(*[m.delete() for m in self._messages[1:]])
                except (discord.NotFound, discord.Forbidden, IndexError, ValueError):
                    pass

            if r & CancelAction.REMOVE_INVOCATION:
                try:
                    await self.invoked_by.delete()
                except (discord.NotFound, discord.Forbidden, IndexError, ValueError):
                    pass

        finally:
            self.is_ready.clear()
            self.is_finished.set()

            # Remove the listeners.
            try:
                self.bot.remove_listener(self._on_message_delete)
            except Exception:
                _logger.exception("Exception on removing listener on_message_delete", exc_info=True)

            try:
                self.bot.remove_listener(self._on_reaction_add)
            except Exception:
                _logger.exception("Exception on removing listener on_reaction_add", exc_info=True)

    async def _permission_error(self):
        try:
            _logger.warning(
                "Permission error occurred for message %s " "requested by %s in %s: %s",
                self.root_message,
                self.invoked_by.author,
                self.invoked_by.guild,
                self.invoked_by.channel,
            )
            await self.channel.send(
                "I lack the required permissions to display this content.\n\n"
                "At the very least, I require the ability to **manage messages**, **add "
                "reactions**, and potentially to use **external emojis**."
            )
        except Exception:
            _logger.exception(
                "Another exception occurred when handling a permission error!", exc_info=True
            )
        raise CancelIteration(CancelAction.REMOVE_ALL_MESSAGES)


class StringNavigator(BaseNavigator[str]):
    # noinspection PyUnresolvedReferences
    """
    Navigator for string content.

    Navigation for a set of pages, given a set of button objects to display as reactions.

    Implementation that takes a collection of string chunks, sending the first to
    a given channel. It then displays a set of reactions on the message that when
    the user interacts with them, it will change the content of the message.

    This emulates an interface that allows "turning of pages" by adding discord
    reactions to the message.

    Args:
        ctx:
            the command context to invoke in response to. If you are using this in
            an event listener, you can generate a ``FakeContext`` to go in here.
        pages:
            A sequence of elements to display.
        buttons:
            A sequence of ``Button`` objects.

    Keyword Args:
        timeout:
            An integer or floating point positive number representing the number of seconds
            to be inactive for before destroying this navigation session. Defaults to 300s
            (5 minutes).
        initial_page:
            The initial page index to start on. Defaults to 0.

    Attributes:
        owner:
            The original user who invoked the event leading to this navigator being displayed.
            Change this to alter who has control over the navigator. Set to None to unlock the
            navigator to all users for control.
        channel:
            The channel we are responding in.
        bot:
            The bot that is sending this paginator. Can be anything derived from discord.Client.
        pages:
            The sequence of pages to display from.
        buttons:
            The ordered mapping of emoji to button for reactions to display.
        timeout:
            The inactive timeout period.
        invoked_by:
            The original invoking message.

    Note:
        Buttons can take control of most parts of this object. To kill the pagination
        early, one should raise a ``CancelIteration`` from the button logic. This exception
        can take an argument that consists of a combination of one or more ``CancelAction``
        enumerations combined via bitwise-or. These flags allow custom specification of what
        to do on cleaning up (e.g. should we delete the root message, or just clear the reactions?)

    Example usage::

        >>> pages = ['page 1', 'page 2']

        >>> nav = StringNavigator(ctx, pages)

        >>> nav.start()

    """

    async def _edit_page(self):
        """|coro|

        Edits the displayed page on Discord. This is the opportunity to add a page number
        to the content if there is room.
        """
        page_header = self.format_page_number()
        content = self.current_page

        if len(content) + len(page_header) <= 2000:
            content = page_header + content

        await self.root_message.edit(content=content[:2000])


class EmbedNavigator(BaseNavigator[discord.Embed]):
    # noinspection PyUnresolvedReferences
    """
    Navigator for embed content.

    Navigation for a set of pages, given a set of button objects to display as reactions.

    Implementation that takes a collection of string chunks, sending the first to
    a given channel. It then displays a set of reactions on the message that when
    the user interacts with them, it will change the content of the message.

    This emulates an interface that allows "turning of pages" by adding discord
    reactions to the message.

    Args:
        ctx:
            the command context to invoke in response to. If you are using this in
            an event listener, you can generate a ``FakeContext`` to go in here.
        pages:
            A sequence of elements to display.
        buttons:
            A sequence of ``Button`` objects.

    Keyword Args:
        timeout:
            An integer or floating point positive number representing the number of seconds
            to be inactive for before destroying this navigation session. Defaults to 300s
            (5 minutes).
        initial_page:
            The initial page index to start on. Defaults to 0.

    Attributes:
        owner:
            The original user who invoked the event leading to this navigator being displayed.
            Change this to alter who has control over the navigator. Set to None to unlock the
            navigator to all users for control.
        channel:
            The channel we are responding in.
        bot:
            The bot that is sending this paginator. Can be anything derived from discord.Client.
        pages:
            The sequence of pages to display from.
        buttons:
            The ordered mapping of emoji to button for reactions to display.
        timeout:
            The inactive timeout period.
        invoked_by:
            The original invoking message.

    Note:
        Buttons can take control of most parts of this object. To kill the pagination
        early, one should raise a ``CancelIteration`` from the button logic. This exception
        can take an argument that consists of a combination of one or more ``CancelAction``
        enumerations combined via bitwise-or. These flags allow custom specification of what
        to do on cleaning up (e.g. should we delete the root message, or just clear the reactions?)

    Example usage::

        >>> pages = [
        ...    discord.Embed(description='page 1'),
        ...    discord.Embed(description='page 2'),
        ... ]

        >>> nav = EmbedNavigator(ctx, pages)

        >>> nav.start()

    Note:
        The custom ``Embed`` class used by this module is
        also compatible here.

    """

    async def _edit_page(self):
        """|coro|

        Edits the displayed page on Discord.
        """
        page_header = self.format_page_number()
        content = self.current_page

        await self.root_message.edit(content=page_header, embed=content)
