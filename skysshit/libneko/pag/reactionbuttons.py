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
    "OwnerT",
    "Button",
    "InvokePredicateT",
    "DisplayPredicateT",
    "CallbackT",
    "button",
    "button_class",
    "default_buttons",
    "first_page",
    "back_10_pages",
    "previous_page",
    "close",
    "next_page",
    "forward_10_pages",
    "last_page",
    "input_number",
    "lock_unlock",
)

import asyncio
import inspect
from typing import Any, Callable, Optional

import discord
from discord.ext import commands
from discord.ext.commands import converter

from libneko import funcmods
from libneko import logging

# Navigator object owning the button instance.
from . import navigator

_logger = logging.get_logger("libneko.pag.reactionbuttons")

OwnerT = Any


class Button:
    def display_if(self, *_, **__):
        ...

    def invoke_if(self, *_, **__):
        ...

    ...


InvokePredicateT = Callable[[Button, discord.Reaction, discord.User], bool]
DisplayPredicateT = Callable[[Button], bool]
CallbackT = Callable[[Button, discord.Reaction, discord.User], None]


class Button:
    """
    Both the callback and predicates can be either coroutines or functions. They
    will automatically be converted to coroutine types if they are not already.

    Navigators and controls are expected to set the ``owner`` attribute.

    Args:
        callback: a function that takes three arguments:
            this button object, the reaction invoking this button, and
            the user who invoked it. May be a coroutine. If it is not, it is
            implicitly converted. This may not be a staticmethod or a
            lambda expression.

    Keyword Args:
        emoji: the unicode emoji character sequence to use on the button.
        name: optional custom name. This exists to add further functionality,
            such as a help utility. Currently, nothing relies on this property
            in libneko. It defaults to the callback function name.

    Attributes:
        description: the docstring of the callback, or emptystring.
        
    """

    def __init__(self, callback: CallbackT, *, emoji: str, name: Optional[str] = None) -> None:
        #: Callback to invoke when the button is clicked.
        self.callback = funcmods.ensure_coroutine_function(callback)
        #: Button name or the callback name if no name was specified.
        self.name = name or callback.__name__
        #: The emoji string to use.
        self.emoji = emoji
        #: The button description. This defaults to the docstring of the callback.
        self.description = inspect.cleandoc(inspect.getdoc(callback) or "")
        self._display_conditions = []
        self._invoke_conditions = []
        #: Navigator that owns this button.
        self.owner: navigator.BaseNavigator = None

    def invoke_if(self, predicate: InvokePredicateT) -> InvokePredicateT:
        """
        Decorates a predicate that determines if the button should respond to
        a given reaction.

        This predicate takes the same signature that ``Client.on_reaction_add``
        would, but a reference to this button object is the first parameter.
        Unless all predicates return True, then we do not invoke the button.

        Access the owner navigation state via the button's ``owner`` attribute.
        """
        coro = funcmods.ensure_coroutine_function(predicate)
        self._invoke_conditions.append(coro)
        return predicate

    def display_if(self, predicate: DisplayPredicateT) -> DisplayPredicateT:
        """
        Decorates a predicate that determines if the button should display.

        This predicate takes this button instance as the only parameter. Access
        the owner navigation state via the button's ``owner`` attribute.

        Unless all predicates return True, then we do not display the
        button. It is not recommended to alter this condition a lot, as we
        """
        coro = funcmods.ensure_coroutine_function(predicate)
        self._display_conditions.append(coro)
        return predicate

    async def should_show(self) -> bool:
        """|coro|

        Return true if the button should display.

        This is evaluated from the stored display predicates.
        If no predicates are present, it returns True.
        """
        for coro in self._display_conditions:
            if not await coro(self):
                return False
        return True

    async def invoke(self, reaction: discord.Reaction, user: discord.User) -> None:
        """|coro|

        Invokes the callback if all predicates for invocation are True.

        If there are no invocation predicates, then we always invoke the
        callback, regardless.
        """
        for coro in self._invoke_conditions:
            if not await coro(self, reaction, user):
                return
        await self.callback(self, reaction, user)


def button(*, emoji: str, name: str = None):
    """
    Shorthand decorator for ``Button`` instantiation.

    Keyword args:
        name: optional button name.
        emoji: the emoji to show.

    Note:
        This decorator creates single-use ``Button`` singletons
        (a.k.a. objects). To quickly create a multiple-use class
        definition, see ``button_class``.

    Example usage::
    
        # The following example shows a button that only
        # triggers if more than one page exists. When clicked,
        # it will raise a CancelIteration to kill the paginator
            
        @button('\N{OK HAND SIGN}')
        async def cancel_btn(btn, reaction, user):
            '''Close the pagination.'''
            raise navigator.CancelIteration
        
        @cancel_btn.invoke_if
        async def cancel_btn_invoke_if(btn, reaction, user):
            '''Only invoke if more than one page exists.'''
            return len(btn.owner) > 1
            
        ...
        
        buttons = [cancel_btn]

    """

    def decorator(coro):
        """Decorates a coroutine to make it into a button."""
        return Button(coro, emoji=emoji, name=name)

    return decorator


def button_class(*, name=None, emoji):
    """
    A button class factory method. This is used to create stateful custom button
    definitions in this file. If you want, you can use it elsewhere if it suits
    your design use case.

    Keyword Args:
         name: Optional button name.
         emoji: Required emoji to react with.

    Returns:
        A class for a button.

    Note:
        If ``button`` is a decorator that produces a specific button
        object, then this will be a decorator that produces a class
        for a button with the given callback. Use ``button`` for
        singleton instances (where you generate the button definitions
        as you require them). Use this ``button_class`` to produce a
        class that you can create multiple instances of the same button
        definition from.

        To add ``display_if`` and ``invoke_if`` listeners to this
        class template, the object returned from this decorator call
        has two attributes: ``proto_display_if`` and ``proto_invoke_if``
        which perform the same operation that the singleton verisons
        do. See the following example for usage to compare with that
        of ``button``.

    Example usage::

        @button_class('\N{OK HAND SIGN}')
        async def cancel_btn(btn, reaction, user):
            '''Close the pagination.'''
            raise navigator.CancelIteration

        @cancel_btn.proto_invoke_if
        async def cancel_btn_invoke_if(btn, reaction, user):
            '''Only invoke if more than one page exists.'''
            return len(btn.owner) > 1

        ...

        # Notice the call operator is used to instantiate it.
        buttons = [cancel_btn()]
    """

    def decorator(coro):
        """Decorates a coroutine."""

        class __MetaButton(Button):
            __name__ = "Button"
            __doc__ = coro.__doc__ or ""
            __qualname__ = "Button"

            _proto_display_ifs = []
            _proto_invoke_ifs = []

            def __init__(self):
                super().__init__(coro, name=name, emoji=emoji)
                for coro_ in self._proto_display_ifs:
                    self.display_if(coro_)
                for coro_ in self._proto_invoke_ifs:
                    self.invoke_if(coro_)

            @classmethod
            def proto_display_if(cls, coro_):
                """|coro|

                Adds a callback to be added to each instance of the button created.
                """
                cls._proto_display_ifs.append(coro_)
                return coro_

            @classmethod
            def proto_invoke_if(cls, coro_):
                """|coro|

                Adds a callback to be added to each instance of the button created.
                """
                cls._proto_invoke_ifs.append(coro_)
                return coro_

        __MetaButton.__doc__ = coro.__doc__ or ""
        return __MetaButton

    return decorator


@button_class(emoji="\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}")
async def first_page(btn: Button, _react: discord.Reaction, _user: discord.User):
    """Button that navigates to the first page."""
    btn.owner.page_index = 0


@first_page.proto_display_if
async def _first_page_display_if(btn):
    return len(btn.owner) > 3


@button_class(emoji="\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}")
async def back_10_pages(btn: Button, _react: discord.Reaction, _user: discord.User):
    """Navigates back 10 pages."""
    btn.owner.page_index -= 10


@back_10_pages.proto_display_if
async def _back_10_pages_display_if(btn):
    return len(btn.owner) > 10


@button_class(emoji="\N{BLACK LEFT-POINTING TRIANGLE}")
async def previous_page(btn: Button, _react: discord.Reaction, _user: discord.User):
    """Navigates back one page."""
    btn.owner.page_index -= 1


@previous_page.proto_display_if
async def _previous_page_display_if(btn):
    return len(btn.owner) > 1


@button_class(emoji="\N{REGIONAL INDICATOR SYMBOL LETTER X}")
async def close(_btn: Button, _react: discord.Reaction, _user: discord.User):
    """Closes the navigation, deletes all messages associated with it."""
    raise navigator.CancelIteration(navigator.CancelAction.REMOVE_ALL_MESSAGES)


@close.proto_invoke_if
async def _close_invoke_if(btn, _, user):
    """This button is special in that it will only respond to the author."""
    return user == btn.owner.invoked_by.author


@button_class(emoji="\N{BLACK RIGHT-POINTING TRIANGLE}")
async def next_page(btn: Button, _react: discord.Reaction, _user: discord.User):
    """Navigates to the next page."""
    btn.owner.page_index += 1


@next_page.proto_display_if
async def _next_page_display_if(btn):
    return len(btn.owner) > 1


@button_class(emoji="\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}")
async def forward_10_pages(btn: Button, _react: discord.Reaction, _user: discord.User):
    """Navigates forward 10 pages."""
    btn.owner.page_index += 10


@forward_10_pages.proto_display_if
async def _forward_10_pages_display_if(btn):
    return len(btn.owner) > 10


@button_class(emoji="\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}")
async def last_page(btn: Button, _react: discord.Reaction, _user: discord.User):
    """Navigates to the last page."""
    btn.owner.page_index = -1


@last_page.proto_display_if
async def _last_page_display_if(btn):
    return len(btn.owner) > 3


@button_class(emoji="\N{INPUT SYMBOL FOR NUMBERS}")
async def input_number(btn: Button, _react: discord.Reaction, _user: discord.User):
    """Allows you to enter a number and jump to that page."""
    lock = btn.__dict__.setdefault("lock", asyncio.Lock())

    if lock.locked():
        await btn.owner.send()


@input_number.proto_display_if
async def _input_number_display_if(btn):
    return len(btn.owner) > 3


@button_class(emoji="\N{BUSTS IN SILHOUETTE}")
async def lock_unlock(btn: Button, _react: discord.Reaction, _user: discord.User):
    """
    Allows the author to specify who else can control the navigation.

    \N{BUST IN SILHOUETTE} - Restrict to only the author.
    \N{BUSTS IN SILHOUETTE} - Give someone else ownership.

    Specify `*`` to allow anyone to use it.
    """
    lock = btn.__dict__.setdefault("lock", asyncio.Lock())

    # Prevent spamming this button and causing weird stuff to happen.
    if lock.locked():
        return

    async with lock:
        if btn.owner.owner == btn.owner.invoked_by.author:
            prompt = None
            try:
                prompt = await btn.owner.send(
                    "Enter the member or role to transfer the pagination ownership to."
                    "\n"
                    "Alternatively, reply with `*` to give everyone control, or with `.` to "
                    "cancel.",
                    add_to_list=False,
                )

                def check(message):
                    """Filters the message."""
                    return (
                        message.author == btn.owner.invoked_by.author
                        and message.channel == btn.owner.channel
                    )

                m = await btn.owner.bot.wait_for("message", check=check, timeout=30)
                try:
                    await m.delete()
                finally:
                    m_content = m.content

                try:
                    await prompt.delete()
                except (discord.NotFound, discord.Forbidden):
                    pass

                if m_content == "*":
                    btn.owner.owner = None
                elif m_content.lower() == ".":
                    return
                else:
                    # noinspection PyProtectedMember
                    try:
                        ctx = await btn.owner.bot.get_context(m)
                        member = await converter.MemberConverter().convert(ctx, m_content)
                        if member.bot:
                            await btn.owner.send(
                                "Cannot transfer to a bot.", delete_after=10, add_to_list=False
                            )
                            return
                        else:
                            btn.owner.owner = member
                    except commands.BadArgument:
                        return btn.owner.send(
                            f"{m_content} was not a recognised member.", delete_after=10
                        )

                new_owner = btn.owner.owner or "everyone"
                await btn.owner.send(f"Okay, {new_owner} has control as well as you.")
            except commands.BadArgument:
                await btn.owner.send("Invalid input.", delete_after=10, add_to_list=False)
                return
            except Exception:
                _logger.exception(
                    "Unexpected error occurred. Poke the dev with a stick to fix this properly.",
                    exc_info=True,
                )
            else:
                # Adjust our button in the list in the owner, otherwise it will
                # no longer respond to us...
                del btn.owner.buttons[btn.emoji]
                btn.emoji = "\N{BUST IN SILHOUETTE}"
                btn.owner.buttons[btn.emoji] = btn
            finally:

                # Delete that response.
                if prompt is not None:
                    try:
                        await prompt.delete()
                    except (discord.NotFound, discord.Forbidden):
                        pass
        else:
            # Re-lock
            btn.owner.owner = btn.owner.invoked_by.author
            await btn.owner.send("Okay, only you can control this again.", delete_after=10)
            # Adjust our button in the list in the owner, otherwise it will
            # no longer respond to us...
            del btn.owner.buttons[btn.emoji]
            btn.emoji = "\N{BUSTS IN SILHOUETTE}"
            btn.owner.buttons[btn.emoji] = btn


@lock_unlock.proto_invoke_if
async def _lock_unlock_invoke_if(btn, _, user):
    """This button is special in that it will only respond to the author."""
    return user == btn.owner.invoked_by.author


@lock_unlock.proto_display_if
async def _lock_unlock_display_if(btn):
    # noinspection PyProtectedMember
    return btn.owner.root_message.guild is not None and len(btn.owner) > 1


def default_buttons():
    """
    Generates a bunch of default button instances.
    
    This will return an instance of each of:
    
     - ``first_page``
     - ``back_10_pages``
     - ``previous_page``
     - ``close``
     - ``next_page``
     - ``forward_10_pages``
     - ``last_page``
     - ``lock_unlock``
     
    ...in a tuple in that order.
    
    """
    return (
        first_page(),
        back_10_pages(),
        previous_page(),
        close(),
        next_page(),
        forward_10_pages(),
        last_page(),
        lock_unlock(),
    )
