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
Wraps the Python JSON module and implements load and dump for async file descriptors
provided by aiofiles.
"""
import io
import json
import typing
from json import *

from libneko import funcmods, filesystem

__all__ = json.__all__ + ["aioload", "aiodump", "Json"]

#: Valid JSON types.
#: See: https://github.com/python/typing/issues/182
JSONObject = typing.Dict[typing.AnyStr, typing.Any]
JSONArray = typing.List[typing.Any]
JSONType = typing.Union[int, float, bool, typing.AnyStr, JSONArray, JSONObject, None]


@funcmods.steal_signature_from(load, steal_docstring=True)
async def aioload(fp: filesystem.AsyncFile, *args, **kwargs) -> JSONType:
    """Loads the given object from an async-compatible file object."""
    fp = io.StringIO(await fp.read())
    return loads(fp.getvalue(), *args, **kwargs)


@funcmods.steal_signature_from(load, steal_docstring=True)
async def aiodump(obj: JSONType, fp: filesystem.AsyncFile, *args, **kwargs) -> None:
    """Dumps the given object to an async-compatible file object."""
    buff = io.StringIO(dumps(obj, *args, **kwargs))
    await fp.write(buff.getvalue())
