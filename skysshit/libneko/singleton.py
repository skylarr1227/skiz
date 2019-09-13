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
Singleton pattern implementation for creating unique one-instance objects
from classes on demand.

Note:
    ``class Foo(Singleton)`` is analogus to ``class Foo(metaclass=SingletonMeta)``.

Example usage:

    >>> class Foo(Singleton):
    >>>     def __init__(self):
    >>>         print('Initialising new Foo')

    >>> a = Foo()
    Initialising new Foo
    >>> b = Foo()
    >>>
    >>> a is b
    >>> True

Author:
    Espy/Neko404NotFound

"""

__all__ = ("SingletonMeta", "Singleton")


def _singleton_repr(t: type):
    return f"<{t.__name__} Singleton>"


class SingletonMeta(type):
    """
    Metaclass that enforces the Singleton pattern. Useful for specialising
    sentinel objects, et cetera.
    """

    __singletons = {}

    def __call__(cls):
        if cls in cls.__singletons:
            return cls.__singletons[cls]
        else:
            singleton = super(SingletonMeta, cls).__call__()
            cls.__singletons[cls] = singleton
            return singleton

    def __repr__(cls):
        return _singleton_repr(cls)

    def __eq__(cls, other):
        if isinstance(type(other), cls):
            return True
        elif other is cls:
            return True
        else:
            return False

    def __hash__(cls):
        return super().__hash__()

    __str__ = __repr__


class Singleton(metaclass=SingletonMeta):
    """Less verbose way of implementing a singleton class."""

    __slots__ = ()

    def __repr__(self):
        return _singleton_repr(type(self))

    __str__ = __repr__

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return True
        elif other is self:
            return True
        else:
            return False
