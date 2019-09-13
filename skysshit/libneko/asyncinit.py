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
Mixin that makes the constructor for the class so it must be awaited. Adds an
``__ainit__`` constructor to enable awaiting certain actions during object
construction.

Useful for stuff like initializing asyncpg connection pools in classes deriving
from ``discord.Client`` or ``discord.ext.commands.Bot``.

Author:
    Espy/Neko404NotFound
"""

__all__ = ("T", "TT", "AsyncInit")

import asyncio
import typing

T = typing.TypeVar("T")
TT = typing.Type[T]


class AsyncInit:
    """
    Base class for a class that needs an asynchronous constructor.

    This modifies some internal signatures to force ``__new__`` to return an
    awaitable with the resultant object inside as the result.

    If an ``__ainit__`` dunder is provided, then this will be called and awaited
    internally after ``__init__`` is invoked.

    Example usage::

        import asyncio

        from aiohttp import ClientSession
        from asyncpg import create_pool
        from asyncpg.pool import Pool
        from discord.ext import commands


        class Bot(AsyncInit, commands.Bot):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

                # Should declare these in constructor here, but it is
                # not necesarry.
                self.http_session: ClientSession = None
                self.postgres_pool: Pool = None

            async def __ainit__(self, **kwargs):
                self.http_session = ClientSession()
                self.postgres_pool = await create_pool(...)

        ...

        loop = asyncio.get_event_loop()


        async def init_bot():
            # Obviously we must call this in a coroutine.
            return await Bot(command_prefix='?!')
            
        # Alternatively, from outside a non-running event loop.
        bot = asyncio.get_event_loop().run_until_complete(Bot(command_prefix='?!'))

    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Default ``__init__`` override to fall back to if the user fails to implement a
        synchronous constructor. This prevents errors implicitly calling the
        constructor or missing arguments in the ``__ainit__``.
        """
        try:
            super().__init__(*args, **kwargs)
        except TypeError:
            super().__init__()

    async def __ainit__(self, *args, **kwargs) -> None:
        """
        Default ``__ainit__`` to fall back to if one is not defined elsewhere.
        """
        ...

    @staticmethod
    def __new__(cls, *args, **kwargs) -> typing.Awaitable[T]:
        """Initialise a new instance of this object."""
        # Return a coroutine to be awaited.
        return cls.__anew__(cls, *args, **kwargs)

    @staticmethod
    async def __anew__(cls, *args, **kwargs) -> T:
        """|coro|

        Calls both the __init__ and __ainit__ methods.
        """
        obj = super().__new__(cls)
        cls.__init__(obj, *args, **kwargs)
        if hasattr(cls, "__ainit__"):
            cls.__ainit__ = asyncio.coroutine(cls.__ainit__)
            await cls.__ainit__(obj, *args, **kwargs)
        return obj

    if typing.TYPE_CHECKING:
        # Mutes errors caused by the fact we are doing voodoo with __new__
        def __await__(self, *args, **kwargs) -> T:
            return self
