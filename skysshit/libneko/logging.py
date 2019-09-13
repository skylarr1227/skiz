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
import inspect

__all__ = (
    "Log",
    "CRITICAL",
    "FATAL",
    "ERROR",
    "WARNING",
    "WARN",
    "INFO",
    "DEBUG",
    "NOTSET",
    "get_logger",
    "basic_config",
)

import logging
from logging import CRITICAL, FATAL, ERROR, WARNING, WARN, INFO, DEBUG, NOTSET


class _LoggerProperty:
    """Only generates the logger once we refer to it for the first time."""

    __slots__ = ("_logger",)

    def __get__(self, instance, owner):
        if not hasattr(self, "_logger"):
            name = owner.__qualname__
            setattr(self, "_logger", logging.getLogger(name))
        return self._logger


class Log:
    """
    Class mixin that injects a logger object into the derived class.

    Example usage::

        >>> class Foo(Log):
        ...    def bar(self):
        ...        self.log.info('In bar!')
        ...    @classmethod
        ...    def baz(cls):
        ...        cls.log.info('In baz!')

        >>> Foo().bar()
        Foo:INFO:In bar!
        >>> Foo.baz()
        Foo:INFO:In baz!

    """

    log: logging.Logger

    def __init_subclass__(cls, **kwargs):
        """Init the logger."""
        cls.log: logging.Logger = _LoggerProperty()


def logger_for(file, object):
    """
    Gets a logger for a given object.

    Usage is::

        >>> class Foo:
        ...     LOGGER = logger_for(__file__, 'Foo')

        >>> class Bar:
        ...     def __init__(self):
        ...         self.logger = logger_for(__file__, type(self))

    """
    module = inspect.getmodulename(file)

    if isinstance(object, type):
        object = object.__qualname__

    name = " ".join((module, object)).strip().replace(" ", ".")
    return logging.getLogger(name)


get_logger = logging.getLogger

basic_config = logging.basicConfig
