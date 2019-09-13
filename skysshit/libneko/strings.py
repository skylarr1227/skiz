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
    Espy / Neko404NotFound
"""

__all__ = ("join", "SensitiveStr", "camelcase_prettify", "cap_start", "format_seconds")

import re
from datetime import datetime


def join(separator: str, iterable, *, cast=str) -> str:
    """
    Join a bunch of items together into a string using the given separator.

    This is the same as str.join, except it casts to string first for you, as
    that kind of makes sense.

    A custom cast method can be provided to override how we obtain the strings.
    By default, it calls the ``str`` builtin. You may wish to change this to
    ``repr`` or something else occasionally.
    """
    iterable = map(cast, iterable)
    return separator.join(iterable)


class SensitiveStr(str):
    """
    Wrapper for sensitive info that blocks the str and repr methods by default.
    To get the underlying string, use the call operator on this object. The reason
    for doing this is to prevent echoing confidential or sensitive data in an
    exec call by accident.
    """

    __slots__ = ()

    # For the json2dataclass implementation.
    __unmarshall__ = True

    def __str__(self) -> str:
        return "<hidden>"

    def __repr__(self) -> str:
        return "<SensitiveStr value=hidden>"

    def __call__(self) -> str:
        return super().__str__()


def cap_start(s: str):
    """Ensures a capital letter at the start, and everywhere else lowercase."""
    return f"{s[0].upper()}{s[1:].lower()}" if s else s


def camelcase_prettify(s: str):
    """delimits on caps in a camelcase string"""
    return cap_start(" ".join(re.findall(r"[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))", s)))


def format_seconds(total_seconds: float, *, precision: int = None) -> str:
    """
    Formats a number of seconds into meaningful units.

    If precision is specified as an int, then only this many of the largest
    non-zero units will be output in the string. Else, all will::

        >>> age = datetime.utcnow() - user.created_at
        >>> age_string = format_seconds(age.total_seconds(), precision=3)
        >>> print(age_string)
        33 days, 14 minutes, 12 seconds

    """

    mins, secs = divmod(total_seconds, 60)
    hrs, mins = divmod(mins, 60)
    days, hrs = divmod(hrs, 24)
    months, days = divmod(days, 30)
    years, months = divmod(months, 12)

    fmt = lambda n, word: n and f'{n:.0f} {word}{int(n) - 1 and "s" or ""}' or ""

    queue = [
        fmt(years, "year"),
        fmt(months, "month"),
        fmt(days, "day"),
        fmt(hrs, "hour"),
        fmt(mins, "minute"),
        fmt(secs, "second"),
    ]
    queue = [*filter(None, queue)]

    if precision:
        queue = queue[:precision]

    return ", ".join(queue) or "just now"


def _sync_pretty_list(iterable, sep, to_s):
    """
    The actuall pretty list function.
    """
    return sep.join(map(to_s, iterable))


async def _async_pretty_list(async_iterable, sep, to_s):
    """
    It makes a list out of an async iterable.
    """
    iterable = []
    async for item in async_iterable:
        iterable.append(item)
    return _sync_pretty_list(iterable, sep, to_s)


def pretty_list(iterable, *, sep, to_s=str):
    """
    It will "prettify" a iterable being an async on or not.
    Author:
        Tmpod

    Changes:
        v0.0.21 - Moved from ``libneko.other`` to ``libneko.strings``.
    """
    if hasattr(iterable, "__anext__"):
        return _async_pretty_list(iterable, sep, to_s)
    else:
        return _sync_pretty_list(iterable, sep, to_s)
