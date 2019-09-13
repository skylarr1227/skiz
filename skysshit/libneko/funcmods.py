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
Contains a bunch of stuff for code metadata, bits and pieces for inspecting
functions and coroutines, helpers for generating documentation quickly, modifying
the apparent signatures of callables, various decorators, and debugger helpers.

Note:
    This is designed to extend and work in-place of Python's :mod:`functools`.

Author:
    Espy/Neko404NotFound
"""

__all__ = (
    "is_coroutine_function",
    "is_coroutine",
    "is_async_def_coroutine",
    "is_async_def_function",
    "is_generator_coroutine_function",
    "is_generator_coroutine",
    "ensure_coroutine_function",
    "steal_signature_from",
    "steal_docstring_from",
    "wraps",
    "print_result",
)

import asyncio
import functools
import inspect
import typing


# True for both old-style and new-style coroutines (generators and async-defs)
def is_coroutine_function(what):
    """
    Returns true for any ``@asyncio.coroutine``\\-decorated or ``async`` function.
    """
    return asyncio.iscoroutinefunction(what)


def is_coroutine(what):
    """
    Returns true for any coroutine produced by  an ``@asyncio.coroutine``\\-decorated or ``async`` function.
    """
    return asyncio.iscoroutine(what)


def is_async_def_function(what):
    """
    Returns true for any ``async def`` function.
    """
    return inspect.iscoroutinefunction(what)


def is_async_def_coroutine(what):
    """
    Returns true for any coroutine produced by an ``async def`` function.
    """
    return inspect.iscoroutine(what)


def is_generator_coroutine_function(what):
    """Returns True if this is a generator coroutine function, not an async def."""
    return not is_async_def_function(what) and is_coroutine_function(what)


def is_generator_coroutine(what):
    """Returns True if this is a generator coroutine, but not an async def one."""
    return not is_async_def_coroutine(what) and is_coroutine(what)


coroutine_param_t = typing.TypeVar("coroutine_param_t", covariant=True)
coroutine_return_t = typing.TypeVar("coroutine_return_t", covariant=True)


class Coroutine(typing.Generic[coroutine_return_t], typing.Awaitable[coroutine_return_t]):
    """Alias for an awaitable result of calling a coroutine."""

    def __await__(self) -> coroutine_return_t:
        ...


# noinspection PyAbstractClass
class CoroutineFunction(
    typing.Generic[coroutine_param_t, coroutine_return_t],
    typing.Coroutine[coroutine_param_t, None, coroutine_return_t],
):
    """Generic type for representing a coroutine function simply."""

    def __call__(self, *args: coroutine_param_t, **kwargs) -> Coroutine[coroutine_return_t]:
        ...


def ensure_coroutine_function(func) -> CoroutineFunction:
    """
    Ensures the given argument is awaitable. If it is not, then we wrap it in a
    coroutine function and return that.

    Example usage::

        >>> async def foo():
        ...    ...

        >>> def bar():
        ...    ...

        >>> fns = (foo, bar)

        >>> for f in fns:
        ...    await ensure_coroutine_function(f)()
    """
    if is_coroutine_function(func):
        return func
    else:

        @wraps(func)
        async def coroutine_fn(*args, **kwargs):
            """Wraps the function in a coroutine."""
            return func(*args, **kwargs)

        return coroutine_fn


def steal_signature_from(original_func, *, steal_docstring=True):
    # noinspection PyUnresolvedReferences
    """
    Makes a decorator that will replace original_func with the decorated argument.

    The decorated argument will have the same apparent signature as the initial
    function, which is useful for defining decorators, etc.

    Example usage::

        >>> def foo(a, b, c, d):
        ...    ...

        >>> @steal_signature_from(foo)
        ... def bar(*args, **kwargs):
        ...    print(foo, args, kwargs)
        ...    return foo(*args, **kwargs)

        >>> inspect.signature(bar)
        (a, b, c, d)

    Parameters:
        original_func:
            The original function to steal from.
        steal_docstring:
            Defaults to True. Specifies whether the docstring should be appended
            to the new function's existing docstring.

    See:
        :func:`steal_docstring_from`

    """

    def decorator(new_func):
        """Decorates the function with the original_func signature."""
        # Update the signature
        orig_sig = inspect.signature(original_func)
        setattr(new_func, "__signature__", orig_sig)

        if steal_docstring:
            new_doc = getattr(new_func, "__doc__") or ""
            new_doc += "\n\n"
            new_doc += inspect.getdoc(original_func) or ""
            new_doc = new_doc.lstrip()
            setattr(new_func, "__doc__", new_doc)

        return new_func

    return decorator


def steal_docstring_from(original_docable, *, mode="replace"):
    # noinspection PyUnresolvedReferences
    """
    Makes a decorator that will replace or append ``original_docable``'s  docstring with
    the docstring of whatever is decorated.

    Example usage::

        >>> def foo(a, b, c, d):
        ...    '''Hello, World!'''
        ...    ...

        >>> @steal_docstring_from(foo, mode='replace')
        ... def bar(*args, **kwargs):
        ...    '''Sausage'''
        ...    print(foo, args, kwargs)
        ...    return foo(*args, **kwargs)

        >>> @steal_docstring_from(foo, mode='append')
        ... def baz(*args, **kwargs):
        ...    '''Mushroom'''
        ...    print(foo, args, kwargs)
        ...    return foo(*args, **kwargs)

        >>> inspect.cleandoc(inspect.getdoc(bar))
        'Hello, World!'
        >>> inspect.cleandoc(inspect.getdoc(baz))
        'Hello, World!\n\nMushroom'

    Parameters:
        original_docable:
            The original item to use the docstring from.
        mode:
            Defaults to ``'replace'``, and must be either ``'replace'`` ``prepend``, or
            ``'append'``.
            This defines the strategy for altering the decorated item's docstring. If it is set to
            ``'replace'`` then it merely overwrites the existing docstring with the one from the
            ``original_docable`` parameter. If it is ``'append'``, then it is appended to the
            end of the super object's docstring after two newline characters. If it is ``prepend``,
            then it will be added before the before the super object's docstring followed by two
            newline characters.
    """

    def decorator(new_docable):
        """Decorates the given element."""
        if mode == "replace":
            new_docable.__doc__ = inspect.getdoc(original_docable)
        elif mode == "append":
            original_doc = inspect.getdoc(original_docable) or ""
            original_doc += "\n\n"
            original_doc += inspect.getdoc(new_docable) or ""
            new_docable.__doc__ = original_doc
        elif mode == "prepend":
            original_doc = inspect.getdoc(new_docable) or ""
            original_doc += "\n\n"
            original_doc += inspect.getdoc(original_docable) or ""
            new_docable.__doc__ = original_doc
        else:
            raise ValueError(f"Did not recognise strategy {mode!r}. Must be `append` or `replace`.")

        return new_docable

    return decorator


def wraps(original_func):
    # noinspection PyUnresolvedReferences
    """
    Similar to the implementation of functools.wraps, except this preserves the
    asynchronous traits of a function where applicable.

    Produces a decorator to decorate a replacement function with.

    References:
        https://www.python.org/dev/peps/pep-0362/#visualizing-callable-objects-signature

    Example usage:

        >>> def print_invocation(fn):
        ...     @wraps(fn)
        ...     def wrapper(*args, **kwargs):
        ...         print('Calling', fn.__name__, 'with', args, kwargs)
        ...         return fn(*args, **kwargs)
        ...     return wrapper
        ...
        ... @print_invocation
        ... def foo(bar, baz):
        ...    return bar + baz

        >>> foo.__name__
        foo

        >>> inspect.signature(foo)
        (bar, baz)

    """

    def decorator(new_func):
        """
        Replaces the decorated function with a signature closer to that of
        what was passed to ``wraps``.
        """

        # Ensures coroutine-ness
        if asyncio.iscoroutinefunction(original_func) and not asyncio.iscoroutinefunction(new_func):
            raise TypeError("Cannot replace an async-def with a def")

        return steal_signature_from(original_func, steal_docstring=False)(
            functools.wraps(original_func)(new_func)
        )

    return decorator


def print_result(func):
    """
    Decorates some callable to dump invocation info to the console
    before executing.


    """
    if is_async_def_function:

        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            print(f"coro {func}", *args, kwargs, "->", result)
            return result

    else:

        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            print(f"func {func}", *args, kwargs, "->", result)
            return result

    return wrapper


partial = functools.partial
total_ordering = functools.total_ordering
cmp_to_key = functools.cmp_to_key


class _StaticMeta(type):
    def __call__(cls, *args, **kwargs):
        raise RuntimeError("This class is static-only")


class StaticOnly(metaclass=_StaticMeta):
    """Makes a class behave as if it is only for class and static-methods."""

    def __new__(cls, *args, **kwargs):
        raise RuntimeError("This class is static-only")

    def __init__(self):
        raise RuntimeError("This class is static-only")
