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
A super-basic non-blocking lockable file-based cache for key-value pairs. Serializes
as JSON.
"""
import asyncio
import atexit
import os
import textwrap
import time
import typing

from libneko import aiojson, filesystem, logging


class AsyncSimpleDatabase(logging.Log):
    """
    An Asynchronous data store that serializes to a given file using JSON. This
    is a poor-mans database, and should not be used for anything overly significant
    or large. Likewise, it will only support basic JSON-compatible types (dict, int,
    float, str, bool, None, and list).

    It is not thread safe, and not safe to be used by more than one program or instance
    simultaneously. No inter-process locks are implemented.

    This will close automatically on exit where possible.

    Parameters:
        file_name:
            The file to read and write from and to.
        cache_period:
            Optional. How often to write data back to disk.
            If unspecified, then we write to disk on each mutation, and never read automatically;
            this will ensure data is persisted as much as possible, but will be noticeably slower
            under load.
            If set to a number, then the data in-memory is written to disk after this many seconds
            repeatedly until the store is closed.
        loop:
            The asyncio event loop to use. If unspecified, then it defaults to the current event
            loop as dictated by :meth:`asyncio.get_event_loop`.
        expect_no_other_access:
            Defaults to True. If True when cache_period is None, then we never refresh the file from
            disk. Writes will still update the disk, but will do so in the background. This makes
            the cache significantly faster, but will not detect changes to the database on disk if
            changed by another program.

    Example::
        file = AsyncSimpleDatabase('file.json')

        @bot.command()
        async def counter(ctx):
            '''
            This command stores a counter for each user in a file.
            All pretty simple. Each time a user calls this, their
            specific counter gets incremented by one.
            '''
            counter = await file.get_or_default(ctx.author.id, 0)
            counter += 1
            await file.set(ctx.author.id, counter)
            await ctx.send(f'Your counter is {counter}')

    Example of use in a context manager::

        async with AsyncSimpleDatabase('file.json') as asd:
            key = await asd.get('hello')

    """

    def __init__(
        self,
        file_name,
        *,
        cache_period: float = None,
        expect_no_other_access=True,
        loop: asyncio.AbstractEventLoop = ...,
    ) -> None:

        self._expect_no_other_access = expect_no_other_access
        self._file_name = file_name
        self._cache = {}
        self._loop = loop if loop is not ... else asyncio.get_event_loop()
        self._lock = asyncio.Lock(loop=self._loop)
        self._cache_task = None
        self._closed = False
        self._at_exit = None

        #: Event to wait for that will fire once data has been loaded for the first time.
        self._ready = asyncio.Event(loop=self._loop)

        # Read from disk as soon as possible.
        reader_task: asyncio.Task = self._loop.create_task(self.read_data_from_disk())
        reader_task.add_done_callback(self._fire_ready)

        if cache_period is not None:
            asyncio.ensure_future(self._auto_cache_job(cache_period))

        self._make_at_exit()

        super().__init__()

    def _fire_ready(self, future: asyncio.Future) -> None:
        ex = future.exception()
        if ex:
            raise ex
        else:
            self._ready.set()

    def _make_at_exit(self) -> None:
        """Ensures we close this gracefully using the atexit module."""

        @atexit.register
        def _at_exit():
            self.close()

        self._at_exit = _at_exit

    async def _auto_cache_job(self, cache_period) -> None:
        self.log.info("Started auto-cache job. This will fire every %s seconds...", cache_period)

        task = asyncio.Task.current_task()
        assert task is not None, "Something is seriously fubared in Libneko's code!"
        self._cache_task = task

        while True:
            try:
                await asyncio.sleep(cache_period)
                if self._closed:
                    raise asyncio.CancelledError("Object was closed.")
                else:
                    await self.write_to_disk()
            except Exception as ex:
                if isinstance(ex, asyncio.CancelledError):
                    self.log.warning("auto-cache job has been cancelled.")
                    self._cache_task = None
                    return
                else:
                    self.log.exception(
                        "An unexpected error occurred and was ignored... data "
                        "was not written to disk"
                    )

    async def _ensure_not_closed_and_ready(self) -> None:
        if self._closed:
            raise ValueError(f"Cannot use a closed {type(self).__name__}")
        else:
            if self._expect_no_other_access and not self.is_auto_caching:
                await self.read_data_from_disk()
            await self._ready.wait()

    async def read_data_from_disk(self) -> None:
        """Reads the most recent data stored on disk, replacing anything currently in memory."""
        if not os.path.exists(self._file_name):
            await self._unsafe_write()

        async with self._lock, filesystem.aioopen(self._file_name) as fp:
            start = time.monotonic()
            obj = await aiojson.aioload(fp)
            end = time.monotonic()

            if not isinstance(obj, dict):
                raise TypeError(
                    f"Expected dict in {self._file_name}, " f"received {type(obj).__name__}"
                )

            self.log.info(f"Serialized from {self._file_name} in {(end - start) * 1_000_000:.2f}µs")

            self._cache = obj

    async def _unsafe_write(self) -> None:
        async with filesystem.aioopen(self._file_name, "w") as fp:
            start = time.monotonic()
            await aiojson.aiodump(self._cache, fp)
            end = time.monotonic()
            self.log.info(f"Serialized to {self._file_name} in {(end - start) * 1_000_000:.2f}µs")

    async def write_to_disk(self) -> None:
        """Writes the most recent data to disk from memory, destroying anything on disk."""
        async with self._lock:
            await self._unsafe_write()

    @property
    def is_ready(self) -> bool:
        """Returns True if the object is ready, or false otherwise."""
        return self._ready.is_set()

    async def wait_for_ready(self) -> None:
        return await self._ready.wait()

    @property
    def is_auto_caching(self) -> bool:
        """
        Returns True if we are caching periodically, or False if we serialize whenever we mutate.
        """
        return self._cache_task is not None

    @property
    def is_closed(self) -> bool:
        """Returns True if this object is considered to be dead and no longer up-to-date."""
        return self._closed

    async def get(self, key: typing.AnyStr) -> aiojson.JSONType:
        """
        Returns the value at the given key, or raises a KeyError if it is not present.
        """
        await self._ensure_not_closed_and_ready()
        async with self._lock:
            return self._cache[key]

    async def get_or_default(
        self, key: typing.AnyStr, default: typing.Any = None
    ) -> aiojson.JSONType:
        """
        Similar to :meth:`get`, but returns `default` instead if nothing is found. If unspecified,
        then `default` defaults to None.
        """
        try:
            return await self.get(key)
        except KeyError:
            return default

    async def set(self, key: typing.AnyStr, value: aiojson.JSONType) -> None:
        """
        Sets the value at the given key.
        """
        await self._ensure_not_closed_and_ready()
        async with self._lock:
            self._cache[key] = value

            if not self.is_auto_caching:
                await self._unsafe_write()

    async def delete(self, key: typing.AnyStr, ignore_missing: bool = False) -> None:
        """
        Deletes the key.

        Parameters:
            key:
                The key to delete.
            ignore_missing:
                Defaults to False. If True, then any missing key is ignored. If False,
                a KeyError is raised instead.
        """
        await self._ensure_not_closed_and_ready()
        async with self._lock:
            try:
                del self._cache[key]
            except KeyError as ex:
                if not ignore_missing:
                    raise ex from None
            else:
                await self._unsafe_write()

    async def size(self) -> int:
        """Returns the number of items in the collection."""
        await self._ensure_not_closed_and_ready()
        async with self._lock:
            return len(self._cache)

    def keys(self) -> typing.KeysView[str]:
        """Returns a copy of any keys. These will not be updated with this object."""
        return self._cache.keys()

    def values(self) -> typing.ValuesView[aiojson.JSONType]:
        """Gets the value view from cache."""
        return self._cache.values()

    def items(self) -> typing.ItemsView[str, aiojson.JSONType]:
        """Gets the item view from cache."""
        return self._cache.items()

    def __contains__(self, item: typing.Any) -> bool:
        """Determine if a key exists at the current point in time in the cache."""
        return item in self._cache

    def close(self) -> None:
        if self._cache_task:
            try:
                self._cache_task.cancel()
            except Exception:
                pass
            self._cache_task = None

        self._closed = True
        atexit.unregister(self._at_exit)

    def dump(self, indent="    ") -> str:
        """Dumps a string representation of the cache."""
        return _recurse_print(self._cache, indent)

    def __str__(self):
        return self.dump()


def _recurse_print(obj, indent):
    if isinstance(obj, list):
        buff = [_recurse_print(item, indent) for item in obj]
        buff = [textwrap.indent(repr(item), indent) for item in buff]
        return "[\n" + textwrap.indent(",\n".join(buff), indent) + "\n]"
    elif isinstance(obj, dict):
        buff = [f"{k!r}: {_recurse_print(v, indent)}" for k, v in obj.items()]
        buff = [textwrap.indent(line, indent) for line in buff]
        return "{\n" + textwrap.indent(",\n".join(buff), indent) + "\n}"
    else:
        return repr(obj)
