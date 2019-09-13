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
Author:
    Espy/Neko404NotFound
"""
import abc
import asyncio
import concurrent.futures
import copy
import inspect
import io
import os
import typing

import aiofiles

from libneko.funcmods import steal_docstring_from

__all__ = ("in_this_directory", "AsyncFile", "aioopen", "BufferProtocol")


def in_this_directory(*path: str, stack_depth: int = 0):
    """
    Refers to a path relative to the caller's file's directory.

    Warning:
        This can not be called from a Python interactive interpreter session
        directly, and will raise a :class:`RuntimeError` if this is attempted.
    """
    module, frame = None, None
    try:
        frame = inspect.stack()[1 + stack_depth]
    except IndexError:
        raise RuntimeError("Could not find a stack record. Interpreter has " "been shot.")
    else:
        module = inspect.getmodule(frame[0])

        if not hasattr(module, "__file__"):
            raise RuntimeError(
                "Cannot find a __file__ attribute. This usually occurs because "
                "you are running this function directly from a Python interpreter "
                "interactive session."
            )

        # https://docs.python.org/3/library/inspect.html#the-interpreter-stack
        # If Python caches strings rather than copying when we move them
        # around or modify them, then this may cause a referential cycle which
        # will consume more memory and stop the garbage collection system
        # from working correctly. Best thing to do here is deepcopy anything
        # we need and prevent this occuring. Del the references to allow them
        # to be freed.
        file = module.__file__
        file = copy.deepcopy(file)
        dir_name = os.path.dirname(file)
        abs_dir_name = os.path.abspath(dir_name)
        pathish = os.path.join(abs_dir_name, *path)
        return pathish
    finally:
        del module, frame


BufferProtocol = typing.Union[typing.SupportsBytes, typing.ByteString, typing.AnyStr]


# AsyncIO file interface. Exists purely for documentation; it is never actually used.
class AsyncFile(abc.ABC):
    """
    @proxy_property_directly('closed', 'raw')
    """

    @steal_docstring_from(io.BufferedIOBase.close)
    async def close(self) -> None:
        ...

    @steal_docstring_from(io.BufferedIOBase.flush)
    async def flush(self) -> None:
        ...

    @steal_docstring_from(io.BufferedIOBase.isatty)
    async def isatty(self) -> bool:
        ...

    @steal_docstring_from(io.BufferedIOBase.readable)
    def readable(self) -> bool:
        ...

    @steal_docstring_from(io.BufferedIOBase.read)
    async def read(self, n: int = None) -> typing.AnyStr:
        ...

    @steal_docstring_from(io.BufferedIOBase.read1)
    async def read1(self, n: int = None) -> typing.AnyStr:
        ...

    @steal_docstring_from(io.BufferedIOBase.readinto)
    async def readinto(self, b: BufferProtocol) -> int:
        ...

    @steal_docstring_from(io.BufferedIOBase.readinto1)
    async def readinto(self, b: BufferProtocol) -> int:
        ...

    @steal_docstring_from(io.BufferedIOBase.readline)
    async def readline(self, size: int = ...) -> typing.AnyStr:
        ...

    @steal_docstring_from(io.BufferedIOBase.readlines)
    async def readlines(self, hint: int = ...) -> typing.List[typing.AnyStr]:
        ...

    @steal_docstring_from(io.BufferedIOBase.seek)
    async def seek(self, offset: int, whence: int) -> int:
        ...

    @steal_docstring_from(io.BufferedIOBase.seekable)
    async def seek(self) -> bool:
        ...

    @steal_docstring_from(io.BufferedIOBase.tell)
    async def tell(self) -> int:
        ...

    @steal_docstring_from(io.BufferedIOBase.truncate)
    async def truncate(self, size: int = ...) -> int:
        ...

    @steal_docstring_from(io.BufferedIOBase.writable)
    async def writable(self) -> bool:
        ...

    @steal_docstring_from(io.BufferedIOBase.write)
    async def write(self, b: BufferProtocol) -> int:
        ...

    @steal_docstring_from(io.BufferedIOBase.detach)
    def detatch(self) -> io.RawIOBase:
        ...

    @steal_docstring_from(io.BufferedIOBase.fileno)
    def fileno(self) -> int:
        ...

    @property
    @steal_docstring_from(io.BufferedIOBase.closed)
    def closed(self) -> bool:
        ...

    def __aenter__(self):
        ...

    def __aexit__(self, exc_type, exc_val, exc_tb):
        ...

    def __aiter__(self) -> typing.AsyncIterator[typing.AnyStr]:
        ...

    def __anext__(self) -> typing.AnyStr:
        ...


def aioopen(
    file: str,
    mode: str = "r",
    buffering: int = -1,
    encoding: str = None,
    errors: typing.Any = None,
    newline: typing.Any = None,
    closefd: bool = True,
    opener: typing.Callable[..., int] = os.open,
    *,
    loop: asyncio.AbstractEventLoop = None,
    executor: concurrent.futures.Executor = None,
) -> AsyncFile:
    """
    Opens a file asynchronously and returns an asynchronous file object to
    handle reading and writing without blocking the caller loop.

    Parameters:
        file: the file name to open.
        mode: the file mode to open.
        loop: the asyncio loop to run in. Defaults to the caller loop.
        executor: the concurrent execution service to invoke inside. Defaults to the
                     executor used for the current event loop.
    Returns:
        an asynchronous file object.

    Information:
        For more details on parameters, see :meth:`open`, :meth:`os.popen`, and
        :meth:`aiofiles.open`.

    File mode characters:

        +------------+----------------------------------------------------------------+
        | Character | Meaning                                                         |
        +-----------+-----------------------------------------------------------------+
        | 'r'       | open for reading (default)                                      |
        | 'w'	    | open for writing, truncating the file first                     |
        | 'x'       | open for exclusive creation, failing if the file already exists |
        | 'a'	    | open for writing, appending to the end of the file if it exists |
        | 'b'       | binary mode                                                     |
        | 't'       | text mode (default)                                             |
        | '+'       | open a disk file for updating (reading and writing)             |
        | 'U'       | universal newlines mode (deprecated)                            |
        +-----------+-----------------------------------------------------------------+

    Note:
        This is just a documented proxy to the implementation provided by the `aiofiles` library.
    """
    return aiofiles.open(
        file,
        mode,
        buffering,
        encoding,
        errors,
        newline,
        closefd,
        opener,
        loop=loop,
        executor=executor,
    )
