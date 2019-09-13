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
    Neko404NotFound/Espy
"""
import asyncio

__all__ = (
    "T",
    "SLOTTED_PREFIX",
    "BasePropertyAbc",
    "BasicProperty",
    "basic_property",
    "ReadOnlyProperty",
    "read_only_property",
    "ReadOnlyClassProperty",
    "read_only_class_property",
    "class_property",
    "ClassProperty",
    "ClassType",
    "cached_property",
    "CachedPropertyAbc",
    "InstanceCachedProperty",
    "SlottedCachedProperty",
    "AsyncCachedProperty",
    "AsyncSlottedCachedProperty",
)

import enum
import inspect
from typing import Awaitable, Any, Callable, Type, TypeVar, Union

T = TypeVar("T")

# We use this instead of `_` as it allows properties with names prefixed by
# an underscore to now have to mess around with namespace mangling. For example,
# without this, a property called `_foo` would look to an attribute called
# `__foo`, however, this would upon declaration in slots be renamed to
# `_Klass__foo` due to mangling convention.
SLOTTED_PREFIX = "_p_"
NON_SLOTTED_CORO_PREFIX = "_c_"


class BasePropertyAbc:
    """
    Enables nicer type checking. All properties derive from this.

    .. warning::

        This should never be instantiated directly. It exists purely as a slotted
        abstract base class (it cannot derive from abc.ABC and have slots).
    """

    __slots__ = ()

    def __new__(cls, *args, **kwargs):
        if cls is BasePropertyAbc:
            raise TypeError("Abstract slotted class cannot be instantiated.")
        else:
            return super().__new__(cls)


class BasicProperty(property, BasePropertyAbc):
    """
    This is just a standardisation of the regular Python ``property``, but will
    match ``True`` if compared by instance to the ``LibNekoProperty`` type.
    """

    pass


basic_property = BasicProperty


class ReadOnlyProperty(BasePropertyAbc):
    """
    Read only property. Is slightly more lightweight than regular properties.

    Example usage::

        >>> class X:
        >>>     @ReadOnlyProperty
        >>>     def epoch(self):
        >>>         return 123456789

        >>> X().epoch
        123456789

    """

    __slots__ = ("func",)

    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        if instance is not None:
            return self.func(instance)
        else:
            return self


read_only_property = ReadOnlyProperty


# noinspection PyMethodOverriding
class ReadOnlyClassProperty(BasePropertyAbc):
    """
    Property that latches on as a class method. This must still be accessed
    from an object if you expect it to behave correctly.

    Example usage::

        @ClassProperty
        def bar(cls):
            return hash(cls)

    """

    __slots__ = ("func",)

    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        instance = type(instance) if instance else owner
        return self.func(instance)


read_only_class_property = ReadOnlyClassProperty

# noinspection PyMethodOverriding
ClassProperty = ReadOnlyClassProperty
class_property = ClassProperty


@enum.unique
class ClassType(enum.Enum):
    """Valid class declaration implementations."""

    DICT = enum.auto()
    SLOTS = enum.auto()


def cached_property(class_type: Union[ClassType, str] = ClassType.DICT):
    """
    Generates a decorator for a method that makes it into a cached property.

    Parameters
        class_type:
            The class attribute container type. Generally this is ``DICT``
            (default). If you implement ``__slots__`` in the class and/or all
            base types, then you need to use ``SLOTS``.

    Note
        All cached property values should have a corresponding slotted attribute
        with the same name, preceded with ``_p_``.
        Slotted cached properties with a name ``foo`` would expect a slot called
        ``_p_foo`` to exist.

    Returns
        A decorator for a callable.

    Examples of usage in definitions::

        class Foo:
            @cached_property()
            def bar(self):
                ...

            @cached_property()
            async def baz(self):
                ...

        class Bar:
            __slots__ = ('_p_foo', '_p_baz')
            @cached_property(ClassType.SLOTS)
            def foo(self):
                ...

            @cached_property(ClassType.SLOTS)
            async def baz(self):
                ...

    Examples of usage at runtime::

        >>> class Example:
        ...    @cached_property()
        ...    def eggs(self):
        ...        print('Called eggs')
        ...        return 22

        >>> e = Example()
        >>> e.eggs
        Called eggs
        22
        >>> e.eggs
        22
        >>> e.eggs
        22
        >>> del e.eggs
        >>> e.eggs
        Called eggs
        22

    """
    if isinstance(class_type, str):
        class_type = ClassType[class_type]

    if not isinstance(class_type, ClassType):
        raise TypeError(f"Decorator argument should be ClassType or str, not {class_type.__name__}")

    def wrapper(func):
        is_coro = inspect.iscoroutinefunction(func)

        if class_type == class_type.DICT:
            class_ = AsyncCachedProperty if is_coro else InstanceCachedProperty
        elif class_type == class_type.SLOTS:
            class_ = AsyncSlottedCachedProperty if is_coro else SlottedCachedProperty
        else:
            raise NotImplementedError(f"{class_type} is not supported.")

        return class_(func)

    return wrapper


class CachedPropertyAbc(BasePropertyAbc):
    """
    Cached property base type.

    Enables nicer type checking.

    .. warning::

        This should never be instantiated directly. It exists purely as a slotted
        abstract base class (it cannot derive from abc.ABC and have slots).

    Note:
        You should use the :meth:`cached_property` decorator instead. That will
        pick the correct cached property type to use.

    """

    __slots__ = ()

    def __new__(cls, *args, **kwargs):
        if cls is CachedPropertyAbc:
            raise TypeError("Abstract slotted class cannot be instantiated.")
        else:
            return super().__new__(cls, *args, **kwargs)

    def __get__(self, instance, owner):
        ...

    def __delete__(self, instance):
        ...


class InstanceCachedProperty(CachedPropertyAbc):
    """
    A cached property type.

    Note:
        You should use the :meth:`cached_property` decorator instead. That will
        pick the correct cached property type to use.

    """

    __slots__ = ("func",)

    def __init__(self, func: Callable[[Any], T]):
        self.func = func

    @property
    def __name__(self) -> str:
        """Returns the cache name."""
        return self.func.__name__ or self.func.__qualname__

    def __get__(self, instance: Any, owner: Type) -> T:
        """
        Get the property's cached value, or compute and cache it if it
        is not already cached.

        Parameters
            instance:
                the instance we are a descriptor for.
            owner:
                the owner type of the instance.

        Returns
            the cached value.
        """
        if instance is not None:
            try:
                return instance.__dict__[self.__name__]
            except KeyError:
                try:
                    return instance.__dict__.setdefault(self.__name__, self.func(instance))
                except Exception as ex:
                    raise ex from None
        else:
            return self

    def __delete__(self, instance: object):
        """
        Clears the attribute value from the cache, if it exists.

        Parameters
            instance:
                the object instance we are a descriptor for.
        """
        instance.__dict__.pop(self.__name__, None)


class SlottedCachedProperty(CachedPropertyAbc):
    """
    A cached property type for slotted instances. This will look for a slot with the
    same name, but preceded by an underscore.

    Note:
        You should use the :meth:`cached_property` decorator instead. That will
        pick the correct cached property type to use.

    """

    __slots__ = ("func",)

    def __init__(self, func: Callable[[Any], T]):
        self.func = func

    @property
    def __name__(self) -> str:
        """Returns the slot name."""
        return f"{SLOTTED_PREFIX}{self.func.__name__}"

    def __get__(self, instance: Any, owner: Type) -> T:
        """
        Get the property's cached value, or compute and cache it if it
        is not already cached.

        Parameters
            instance:
                the instance we are a descriptor for.
            owner:
                the owner type of the instance.

        Returns
            the cached value.
        """
        if instance is not None:
            try:
                return getattr(instance, self.__name__)
            except AttributeError:
                try:
                    val = self.func(instance)
                except Exception as ex:
                    raise ex from None
                else:
                    setattr(instance, self.__name__, val)
                    return val
        else:
            return self

    def __delete__(self, instance: object):
        """
        Clears the attribute value from the cache, if it exists.

        Parameters
            instance:
                the object instance we are a descriptor for.
        """
        try:
            delattr(instance, self.__name__)
        except AttributeError:
            pass


class AsyncCachedProperty(CachedPropertyAbc):
    """
    A cached property type that must be awaited.

    Note:
        You should use the :meth:`cached_property` decorator instead. That will
        pick the correct cached property type to use.

    """

    __slots__ = ("func",)

    def __init__(self, func: Callable[[Any], T]):
        self.func = func

    @property
    def __name__(self):
        """Returns the cache name."""
        return self.func.__name__

    def __get__(self, instance: Any, owner: Type) -> Awaitable[T]:
        """
        Get the property's cached value, or compute and cache it if it
        is not already cached.

        Parameters
            instance:
                the instance we are a descriptor for.
            owner:
                the owner type of the instance.
        Returns
            a coroutine to be awaited to retrieve the cached value.
        """
        if instance is None:
            return self
        else:
            if self.__name__ not in instance.__dict__:
                future = asyncio.ensure_future(self.func(instance))
                instance.__dict__[self.__name__] = future
            return instance.__dict__[self.__name__]

    def __delete__(self, instance: Any):
        """
        Clears the attribute value from the cache, if it exists.

        Parameters
            instance:
                the object instance we are a descriptor for.
        """
        instance.__dict__.pop(self.__name__, None)


class AsyncSlottedCachedProperty(CachedPropertyAbc):
    """
    An async cached property type for slotted instances. This will look for a
    slot with the same name, but preceded by an underscore, and must be awaited.

    Note:
        You should use the :meth:`cached_property` decorator instead. That will
        pick the correct cached property type to use.

    """

    __slots__ = ("func",)

    def __init__(self, func: Callable[[Any], T]):
        self.func = func

    @property
    def __name__(self) -> str:
        """Returns the slot name."""
        return f"{SLOTTED_PREFIX}{self.func.__name__ or self.func.__qualname__}"

    def __get__(self, instance: Any, owner: Type) -> Awaitable[T]:
        """
        Get the property's cached value, or compute and cache it if it
        is not already cached.

        Parameters
            instance:
                the instance we are a descriptor for.
            owner:
                the owner type of the instance.
        Returns
            a coroutine to be awaited to retrieve the cached value.
        """
        if instance is None:
            return self
        else:
            if not hasattr(instance, self.__name__):
                future = asyncio.ensure_future(self.func(instance))
                setattr(instance, self.__name__, future)
            return getattr(instance, self.__name__)

    def __delete__(self, instance: object):
        """
        Clears the attribute value from the cache, if it exists.

        Parameters
            instance:
                the object instance we are a descriptor for.
        """
        try:
            delattr(instance, self.__name__)
        except AttributeError:
            pass
