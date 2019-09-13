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
Other utilities.

Author:
    Espy/Neko404NotFound; Davfsa
"""
import collections

__all__ = (
    "find",
    "choice",
    "random_color",
    "random_colour",
    "find_channel",
    "find_general_or_system",
    "ack",
    "perror",
    "patch_in_uvloop",
    "use_proactor_on_windows",
    "ProactorEventLoopPolicy",
)

import asyncio
import random
import re
import sys
import threading
import traceback

import discord
from discord.ext import commands
from discord.utils import find


def choice(*args):
    """
    Wrapper for random.choice that takes variadic arguments. This allows
    iterables and sets to also be used.
    
    Example usage::
        
        x = {1, 2, 3, 4, 5}
        y = choice(*x)
    """
    return random.choice(args)


def random_colour():
    """
    Returns a random colour in the range [0,FFFFFF] as an int.
    """
    return random.randint(0, 0xFFFFFF)


random_color = random_colour


def find_channel(channels, *, match_regex=r"^general$", match_flags=re.I):
    """
    Attempts to find a match for the given channel regex (or ``/^general$/`` by default)
    in the given channel list. If nothing is found, a KeyError is raised.
    
    If the channels list is actually a guild, we will search text channels. The idea
    is to provide a quicker way to find the #general channel by default, since
    default channels no longer exist on Discord.
    """
    if isinstance(channels, discord.Guild):
        channels = channels.text_channels

    rexp = re.compile(match_regex, match_flags)

    channel = find(lambda c: rexp.match(c.name), channels)

    if channel is None:
        raise KeyError(rexp)
    else:
        return channel


def find_general_or_system(guild):
    """
    Gets the system channel, or general. If neither exist, raises a ``KeyError``.
    
    This is literally just an extension of ``find_channel``.
    """
    return getattr(guild, "system_channel", None) or find_channel(guild)


def ack(message, *, react="\N{OK HAND SIGN}", timeout=5, loop=None, me=None):
    """
    Reacts to a message, or replies, to acknowledge an action.

    If message is a context, the loop and me objects are optional.

    This runs asynchronously, nothing is returned.

    Example usage::

        @commands.command()
        async def do_something(ctx):
            do_something_special_here()

            ack(ctx)
    """
    if isinstance(message, commands.Context):
        message, loop, me = message.message, message.bot.loop, message.bot.user

    loop.create_task(_ack(me, react, message, timeout))


async def _ack(me, react, message, timeout):
    """|coro|

    Acknowledges a given message with a given react

    Used internally.
    """
    # noinspection PyBroadException
    try:
        await message.add_reaction(react)
        await asyncio.sleep(timeout)
        await message.remove_reaction(react, me)
    except discord.Forbidden:
        await message.channel.send(react, delete_after=timeout)
    finally:
        return


def perror(*args, **kwargs):
    """
    This is exactly the same as the built-in :meth:`print` method, except that it
    will default to outputting to the standard error stream.
    """
    kwargs.setdefault("file", sys.stderr)
    print(*args, **kwargs)


def patch_in_uvloop():
    """
    uvloop provides a significantly faster asyncio event loop policy than the
    default one provided by Python. The idea is to stick this before you first
    declare your bot if you wish to switch to uvloop specifically::

        >>> from discord.ext import commands
        >>> import libneko

        >>> libneko.patch_in_uvloop()

        >>> bot = commands.Bot(...)

    uvloop is the asynchronous event loop system employed by node.js.

    Warning:
        This will only work on Mac OS X and Linux. Windows is not supported.
        Calling this on Windows will do nothing whatsoever, meaning it is safe
        to use without checking the OS first.

    Note:
        This is also designed to null-op if used with the JVM (e.g. Jython).
    """
    import importlib
    import platform

    os_name = platform.system().lower()

    if os_name not in ("windows", "java"):
        try:
            uvloop = importlib.import_module("uvloop")
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        except (ImportError, ModuleNotFoundError):
            perror("Not supporting uvloop: it is not installed.")
        except Exception:
            perror("Cannot import or configure uvloop:")
            traceback.print_exc()
        else:
            perror(f"Detected {os_name}, successfully changed asyncio policy to use uvloop.")


class ProactorEventLoopPolicy(asyncio.AbstractEventLoopPolicy):
    """
    Implements an event loop per thread.

    Warning:
        This is only compatible with Windows.

    See:
        :func:`use_proactor_on_windows`
    """

    def __init__(self, proactor=None):
        self.__loops = collections.defaultdict(lambda: self.new_event_loop())
        self.__child_watcher = asyncio.get_child_watcher()
        self.__proactor = proactor

    @property
    def _this_thread(self):
        return threading.current_thread()

    @property
    def proactor(self):
        return self.__proactor

    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        return self.__loops[self._this_thread]

    def set_event_loop(self, loop):
        self.__loops[self._this_thread] = loop

    def new_event_loop(self) -> asyncio.AbstractEventLoop:
        return asyncio.ProactorEventLoop(proactor=self.__proactor)

    get_child_watcher = NotImplemented
    set_child_watcher = NotImplemented


def use_proactor_on_windows():
    """
    The default event loop type on Windows will *NOT* support using any of the subprocess
    functions for asyncio. If you wish to use these, then add a call to this patching method
    before you initialise your bot. This will change the event loop to an
    :class:`asyncio.ProactorEventLoop`::

        >>> from discord.ext import commands
        >>> import libneko

        >>> libneko.use_proactor_on_windows()

        >>> bot = commands.Bot(...)

    If we detect an OS that is not Windows, then this call will exit silently.

    Note:
        This is compatible with :func:`libneko.patch_in_uvloop`.
    """
    import platform

    if platform.system().lower() == "windows":
        perror("Detected windows, switching to ProactorEventLoop.")
        asyncio.set_event_loop_policy(ProactorEventLoopPolicy())
