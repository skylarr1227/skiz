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

"""
Custom implementations of :class:`discord.ext.commands.Bot` and
:class:`discord.ext.commands.AutoShardedBot`.

Author:
    Espy/Neko404NotFound
"""

__all__ = ("Bot", "AutoShardedBot", "Context")

import os
import textwrap
import typing
import warnings
from concurrent.futures import thread

import discord as _discord
from discord.ext import commands as _commands

from libneko import commands
from libneko import converters
from libneko import embeds
from libneko import funcmods
from libneko import logging

_magic_number = os.cpu_count() * 5 - 1


class DeprecationWarning(UserWarning):
    """Shadows the internal warning, but isn't muted by default."""

    pass


class Context(_commands.Context):
    @funcmods.steal_docstring_from(converters.clean_content, mode="append")
    @funcmods.steal_docstring_from(_commands.Context.send, mode="prepend")
    async def safe_send(
        self,
        content: typing.Optional[str] = None,
        *,
        tts: bool = False,
        embed: embeds.Embed = None,
        file: _discord.File = None,
        files: typing.List[_discord.File] = None,
        delete_after: typing.Optional[float] = None,
        nonce: typing.Optional[int] = None,
        **cleaner_opts,
    ) -> _discord.Message:
        """
        This is the same as the discord.py :class:`discord.ext.commands.Context` object,
        except for the fact that it also has a :meth:`safe_send` method that you can call
        instead of :meth:`send` if you so choose. The safe_send method takes any additional
        keyword arguments to the :class:`libneko.clean_content` class. These are used to
        scrub any response that is being sent.
        """
        if content is not None:
            content = str(content)
            cc = _commands.clean_content(**cleaner_opts)
            content = await cc.convert(self, content)
        return await super().send(
            content=content,
            tts=tts,
            embed=embed,
            file=file,
            files=files,
            delete_after=delete_after,
            nonce=nonce,
        )


# noinspection PyUnresolvedReferences
class _BotMixin(logging.Log):
    """
    New features:
        A built-in thread pool executor that can have blocking work delegated to
        it either by calling :attr:`run_in_executor` on a function and parameters,
        or by decorating a function/callable in the :attr:`no_block` decorator.

        Default ``command`` and ``group`` implementations use the extended ``libneko``
        definitions from ``libneko.commands``. It is then recommended you use
        ``libneko.commands`` instead of ``discord.ext.commands`` where possible!

    New warnings:
        If you use the ``@event`` decorator, a DeprecationWarning will be raised.
        The reason for this is that using this decorator only allows one event type
        per application to be registered, and it is generally not what you need.

        Keeping to a consistent naming convention is usually a Pythonic way of
        writing code, so I recommend the use of ``@listen()`` instead of ``@event``.
        This additionally allows the specification of a custom event name if you need
        to name the listener function something else, and allows you to dynamically
        remove the event later on during runtime without having to use :func:`delattr`
        to achieve this.

        You can disable the warning by setting the optional keyword argument
        ``ignore_event_decorator_call`` to ``True`` in the constructor call for this
        class.

        There is also a warning that is disabled by specifying ``ignore_overwrite_on_message``
        to be ``True`` that warns you if you accidentally attempt to overwrite the
        default on_message event handler, as this can break any command handling
        functionality for the entire bot unless done correctly. Unless you need to
        adjust the way discord.py handles dispatched on_message events and how it
        turns them into contexts and dispatches the appropriate command, then you do
        not generally need to even touch this.

    Note:
        To disable ALL the custom warnings, you can instead specify the ``shut_up`` kwarg
        flag as being ``True``.

    New events:
        on_run_in_executor(func, args, kwargs):
            Invoked when a job is delegated to the threadpool.
        on_start():
            Invoked when the bot first starts. Does not get passed the token, for
            security reasons.
        on_logout():
            Invoked when the bot logs out.
        on_add_cog(cog):
            Invoked when the bot has a new cog registered.
        on_remove_cog(cog):
            Invoked when the bot unregisters a cog.
        on_extension_load(extension):
            Invoked when the bot loads an extension.
        on_extension_unload(extension):
            Invoked when the bot unloads an extension.
        on_command_add(command):
            Invoked when the bot adds a new command.
        on_command_remove(command):
            Invoked when the bot removes a command.
            
    Warning:
        The logout hooks may not be called on Windows operating systems correctly,
        depending on how they get invoked. Likewise, on Unicies (i.e. OSX and Linux),
        one must ensure that they terminate the bot using a path of control that
        sends at the most a ``SIGTERM`` signal to the bot (i.e. with a single 
        keyboard interrupt). If a ``SIGKILL`` gets triggered, then the logout hook
        will *NOT* run. These are issues that are out of my control. They reside in
        how Python is implemented, and how the operating system's kernel functions
        internally.

    Note:
        These events are usable in exactly the same way as the existing discord.py
        events which are described in the discord.Client Event Reference
        https://discordpy.readthedocs.io/en/rewrite/api.html#event-reference
        and additionally in the discord.ext.commands.Bot Event Reference
        https://discordpy.readthedocs.io/en/rewrite/ext/commands/api.html#event-reference

    Warning:
        The above events are all dispatched **BEFORE** the action is performed, rather
        than after. It is implementation specific and depends how the environment
        is running as to whether this is invoked before, during, or after the actual
        operation the event represents is executing. You should not rely on this
        behaviour for chronological ordering of operations.

    Extra keyword arguments:
        max_workers:
            Optional max number of worker threads to spawn. This is, by default,
            set to a magic number proportional to the number of CPU cores the system
            has, as per the Python recommended implementation. See
            :func:`concurrent.futures.threads.ThreadPoolExecutor` for more details.
            If specified as anything other than ``None``, then that value is used
            instead.
        enable_default_help:
            Enables the help command if True (default) or disables it otherwise.
        ignore_event_decorator_call:
            Mutes the :class:`DeprecationWarning` triggering if you use the ``@event``
            decorator instead of the ``@listen()`` decorator if set to ``True``.
            Defaults to ``False``.
        ignore_overwrite_on_message:
            Raises a warning if we attempt to overwrite the ``on_message`` event
            handler for Discord.py if this is ``False`` (default), otherwise set
            this to ``True``.
        shut_up:
            Mutes all custom warnings raised by libneko.clients.* objects, and
            overrides the other flags. Defaults to ``False``.

    """

    def __init__(
        self,
        *args,
        max_workers: int = None,
        enable_default_help: bool = True,
        ignore_event_decorator_call: bool = False,
        ignore_overwrite_on_message: bool = False,
        shut_up: bool = False,
        **kwargs,
    ):
        self._thread_pool = thread.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix=f"libneko.clients.{type(self).__name__} worker",
        )

        # Update: we do not need this; Python automatically does this anyway.
        # Ensure thread pool shuts down.
        # @atexit.register
        # def kill_pool():
        #    try:
        #        self._thread_pool.shutdown(wait=False)
        #    except Exception:
        #        pass
        self._has_logged_out_triggered = False

        self._ignore_event_decorator_call = ignore_event_decorator_call or shut_up
        self._ignore_overwrite_on_message = ignore_overwrite_on_message or shut_up

        super().__init__(*args, **kwargs)

        if not enable_default_help:
            self.remove_command("help")

    def _run_in_executor(self, func, *args, **kwargs):
        """
        Runs the job in a threadpool, after dispatching the
        ``on_run_in_threadpool(func, args, kwargs)`` event.
        """
        self.dispatch("run_in_threadpool", func, args, kwargs)
        partial = funcmods.partial(func, *args, **kwargs)
        return self.loop.run_in_executor(self._thread_pool, partial)

    @funcmods.steal_docstring_from(_run_in_executor, mode="append")
    def run_in_executor(self, func, *args, **kwargs) -> typing.Awaitable:
        """
        Runs the given blocking function in the object thread pool asynchronously. This allows
        a blocking function to be called inside a coroutine without blocking the entire event
        loop while it is executing.

        This can be used to run blocking libraries such as ``psycopg2`` and ``PIL`` without
        crippling the bot as a result. Note that it is still recommended to instead call
        an existing asyncio-optimised library where possible, as that will have less overhead
        (for example, ``asyncpg`` is a good alternative to ``psycopg2``).

        Parameters:
            func:
                The function to call. Must not be a coroutine function or ``async def``.
            args:
                Positional arguments to call with.
            kwargs:
                Keyword arguments to call with.

        Returns:
            An awaitable future that will, upon completion, contain the result of calling
            ``func`` with the given arguments.

        Example::

            >>> # Note: don't actually ever do this please.
            ... def factorial(n):
            ...     '''Really slow BLOCKING function.'''
            ...     return 1 if n < 2 else n * factorial(n - 1)

            >>> # We can run it via this coroutine like so, and it will not block the current
            >>> # event queue (except for thread-related stuff, but that is up to the Python
            >>> # implementation, specifically).
            >>> @commands.command(name='factorial')
            ... async def factorial_cmd(ctx, number: int):
            ...     '''
            ...     Gets the factorial of the given number and outputs it.
            ...     '''
            ...     async with ctx.typing():
            ...         result = await ctx.bot.run_in_executor(factorial, number)
            ...     result = str(result)
            ...     # Send the first 2000 digits
            ...     await ctx.send(result[:2000])

        See:
            The :func:`no_block` decorator also in this class. This enables directly decorating
            a function to replace it with an awaitable non-blocking coroutine with the same
            signature!
        """
        if funcmods.is_coroutine_function(func):
            raise TypeError("The function must not be marked `@asyncio.coroutine` or `async`")
        elif funcmods.is_coroutine(func):
            raise TypeError("The function cannot be a coroutine. It must be a `def`")
        elif not callable(func):
            raise TypeError(
                "The func parameter must be callable. Are you sure it isn't a "
                "descriptor such as @property, @staticmethod, @classmethod, etc "
                "instead?"
            )

        else:
            return self._run_in_executor(func, *args, **kwargs)

    # noinspection PyUnusedLocal
    @funcmods.steal_docstring_from(_run_in_executor, mode="append")
    def no_block(self, func):
        """
        Similar to :func:`run_in_executor` in that it allows the execution of a function that would
        otherwise block the asyncio event queue as a non-blocking coroutine.

        Parameters:
             func:
                A callable that is not async.

        Returns:
            An ``async def``\\-marked function that should be awaited. When invoked as a coroutine,
            it will invoke the decorated function in a non-blocking coroutine wrapper.
            This allows a blocking function to be called inside a coroutine without blocking the
            entire event loop while it is executing.

        This can be used to run blocking libraries such as ``psycopg2`` and ``PIL`` without
        crippling the bot as a result. Note that it is still recommended to instead call
        an existing asyncio-optimised library where possible, as that will have less overhead
        (for example, ``asyncpg`` is a good alternative to ``psycopg2``).

        Example::

            >>> @bot.no_block
            ... def factorial(n):
            ...    '''Really slow BLOCKING function.'''
            ...   return 1 if n < 2 else n * factorial(n - 1)

            >>> @bot.command(name='factorial')
            ... async def factorial_cmd(ctx, number: int):
            ...    '''
            ...    Gets the factorial of the given number and outputs it.
            ...    '''
            ...    async with ctx.typing():
            ...        result = await factorial(number)
            ...    result = str(result)
            ...    # Send the first 2000 digits
            ...    await ctx.send(result[:2000])


        Info:
            This must decorate a callable (i.e. a non-coroutine function, or an instance of a
            class that implements a non-coroutine version of ``__call__``. It will not work
            otherwise, and will validate what is being decorated before returning the new decorator
            function.

        Warning:
            This will not work well with functions inside the same class definition directly. It
            is suited for other functions that are not members of a class as an instance member,
            static member or class-scoped member, or other descriptors such as properties that
            mangle the ability to directly call a function.

        """
        if funcmods.is_coroutine_function(func):
            raise TypeError("The function cannot be marked `@asyncio.coroutine` or `async`")
        elif funcmods.is_coroutine(func):
            raise TypeError("The function cannot be a coroutine. It must be a `def`")
        elif not callable(func):
            raise TypeError(
                "The decorated item is not callable. Are you sure it isn't a "
                "descriptor such as @property, @staticmethod, @classmethod, etc "
                "instead?"
            )

        @funcmods.steal_signature_from(func)
        async def wrapper(*args, **kwargs):
            return await self._run_in_executor(func, *args, **kwargs)

        return wrapper

    @property
    def executor(self) -> thread.ThreadPoolExecutor:
        """Gets the thread pool executor associated with this bot."""
        return self._thread_pool

    @funcmods.steal_docstring_from(_commands.Bot.start, mode="append")
    @funcmods.steal_signature_from(_commands.Bot.start, steal_docstring=False)
    async def start(self, *args, **kwargs):
        """
        A special implementation of :attr:`discord.ext.commands.Bot.start` that also fires
        an ``on_start()`` event that triggers as before as the :func:`start` or :func:`run`
        methods are called.
        """
        self.dispatch("start")
        return await super().start(*args, **kwargs)

    @funcmods.steal_docstring_from(_commands.Bot.logout, mode="append")
    @funcmods.steal_signature_from(_commands.Bot.logout, steal_docstring=False)
    async def logout(self):
        """
        Triggers the ``on_logout()`` event before logging out.
        """
        if not self._has_logged_out_triggered:
            self.dispatch("logout")
        return await super().logout()

    @funcmods.steal_docstring_from(_commands.Bot.logout, mode="append")
    @funcmods.steal_signature_from(_commands.Bot.logout, steal_docstring=False)
    async def close(self):
        """
        Triggers the ``on_logout()`` event if it was not already triggered by :meth:`logout`
        before.
        """
        if not self._has_logged_out_triggered:
            self.dispatch("logout")
        return await super().close()

    @funcmods.steal_docstring_from(_commands.Bot.add_cog, mode="append")
    @funcmods.steal_signature_from(_commands.Bot.add_cog, steal_docstring=False)
    def add_cog(self, cog):
        """
        Triggers the ``on_add_cog(cog)`` event before a cog is added.
        """
        if not isinstance(cog, _commands.Cog):
            raise RuntimeError(f"The cog {cog} now must derive from discord.ext.commands.Cog to "
                               "be valid.")
        self.dispatch("add_cog", cog)
        return super().add_cog(cog)

    @funcmods.steal_docstring_from(_commands.Bot.remove_cog, mode="append")
    @funcmods.steal_signature_from(_commands.Bot.remove_cog, steal_docstring=False)
    def remove_cog(self, cog):
        """
        Triggers the ``on_remove_cog(cog)`` event before a cog is removed.
        """
        self.dispatch("remove_cog", cog)
        return super().remove_cog(cog)

    @funcmods.steal_docstring_from(_commands.Bot.unload_extension, mode="append")
    @funcmods.steal_signature_from(_commands.Bot.unload_extension, steal_docstring=False)
    def unload_extension(self, extension):
        """
        Triggers the ``on_unload_extension(extension)`` event before an extension is unloaded.
        """
        self.dispatch("unload_extension", extension)
        return super().unload_extension(extension)

    @funcmods.steal_docstring_from(_commands.Bot.load_extension, mode="append")
    @funcmods.steal_signature_from(_commands.Bot.load_extension, steal_docstring=False)
    def load_extension(self, extension):
        """
        Triggers the ``on_load_extension(extension)`` event before an extension is added.
        """
        self.dispatch("load_extension", extension)
        return super().load_extension(extension)

    @funcmods.steal_docstring_from(_commands.Bot.add_command, mode="append")
    @funcmods.steal_signature_from(_commands.Bot.add_command, steal_docstring=False)
    def add_command(self, command):
        """
        Triggers the ``on_add_command(command)`` event before a command is added.
        """
        self.dispatch("add_command", command)
        return super().add_command(command)

    @funcmods.steal_docstring_from(_commands.Bot.remove_command, mode="append")
    @funcmods.steal_signature_from(_commands.Bot.remove_command, steal_docstring=False)
    def remove_command(self, command):
        """
        Triggers the ``on_remove_command(command)`` event before a command is removed.
        """
        self.dispatch("remove_command", command)
        return super().remove_command(command)

    @funcmods.steal_docstring_from(_commands.Bot.command, mode="append")
    def command(self, *args, **kwargs):
        """
        Uses the :class:`libneko.Command` command implementation.
        """
        kwargs.setdefault("cls", commands.Command)
        return super().command(*args, **kwargs)

    @funcmods.steal_docstring_from(_commands.Bot.group, mode="append")
    def group(self, *args, **kwargs):
        """
        Uses the :class:`libneko.Group` group implementation.
        """
        kwargs.setdefault("cls", commands.Group)
        return super().command(*args, **kwargs)

    @funcmods.steal_docstring_from(_commands.Bot.event, mode="append")
    def event(self, coro):
        """
        If you use the ``@event`` decorator, a DeprecationWarning will be raised.
        The reason for this is that using this decorator only allows one event type
        per application to be registered, and it is generally not what you need.

        Keeping to a consistent naming convention is usually a Pythonic way of
        writing code, so I recommend the use of ``@listen()`` instead of ``@event``.
        This additionally allows the specification of a custom event name if you need
        to name the listener function something else, and allows you to dynamically
        remove the event later on during runtime without having to use :func:`delattr`
        to achieve this.

        You can disable the warning by setting the optional keyword argument
        ``ignore_event_decorator_call`` to ``True`` in the constructor call for this.
        """
        if not self._ignore_event_decorator_call:
            warnings.warn(
                textwrap.dedent(
                    f"""
                Usage of `@Bot.event` is deprecated, please use `@Bot.listen()` instead.
                
                Bot.event only allows subscription of a single event of any event type
                (here, {getattr(coro, "__name__", str(coro))}) for the entire bot, and it
                is usually not what you want. 
                
                Bot.listen() allows you to subscribe as many as you like, and matches the
                decorator syntax much more closely to the rest of the discord.ext.commands
                module. Hooray for consistency.
                
                You can disable this message by specifying the `ignore_event_decorator_call`
                argument as `True` when initialising the bot, like so                
                    bot = clients.Bot(..., ignore_event_decorator_call=True)
                or
                    bot = clients.Bot(..., shut_up=True)
                if you are sure you want to do this!
            """
                ),
                category=DeprecationWarning,
                stacklevel=2,
            )

        if not self._ignore_overwrite_on_message and coro.__name__ == "on_message":
            warnings.warn(
                textwrap.dedent(
                    """
                You are overwriting the default on_message event listener. 
                
                This can have undesired side effects such as preventing the entire bot
                from processing any commands, unless you explicitly invoke the process
                yourself, and it is generally not a nice thing to be doing unless you
                need to override the process the bot uses for dispatching commands.
                
                The better alternative is to decorate the coroutine with `Bot.listen()`
                instead of `Bot.event`, as this will not have this side effect.
                
                You can disable this message by specifying the `ignore_overwrite_on_message`
                argument as `True` when initialising the bot, like so
                    bot = clients.Bot(..., ignore_overwrite_on_message=True)
                or
                    bot = clients.Bot(..., shut_up=True)
                if you are sure you want to do this!
            """
                ),
                category=DeprecationWarning,
                stacklevel=2,
            )

        return super().event(coro)

    @funcmods.steal_docstring_from(_commands.Bot.get_context)
    @funcmods.steal_signature_from(_commands.Bot.get_context)
    async def get_context(self, message, *, cls=Context):
        return await super().get_context(message, cls=cls)


@funcmods.steal_docstring_from(_BotMixin, mode="append")
@funcmods.steal_docstring_from(_commands.Bot, mode="replace")
class Bot(_BotMixin, _commands.Bot):
    pass


@funcmods.steal_docstring_from(_BotMixin, mode="append")
@funcmods.steal_docstring_from(_commands.AutoShardedBot, mode="replace")
class AutoShardedBot(_BotMixin, _commands.AutoShardedBot):
    pass
