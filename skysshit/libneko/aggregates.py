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
Various collection types and definitions for useful operations.

Note:
    This is designed to be used in-place of Python's :mod:`collections` library.

Author:
    Espy/Neko404NotFound
"""
import re

__all__ = (
    "SetType",
    "FrozenOrderedSet",
    "MutableOrderedSet",
    "OrderedSet",
    "TwoWayDict",
    "ObservableAsyncQueue",
    "ObservableAsyncQueueType",
    "ValueT",
    "ImmutableProxy",
    "Proxy",
    "TypeSet",
    "PatternSet",
)

import asyncio
import types
from collections import *

import typing

from libneko.properties import cached_property

SetType = typing.TypeVar("SetType")


class FrozenOrderedSet(typing.AbstractSet, typing.Generic[SetType]):
    """
    An ordered unique set implementation that is frozen after definition.

    This uses a tuple underneath. To have mutability, you may use ``MutableOrderedSet``
    instead. That relies on a different internal representation.
    """

    def __init__(self, iterable: typing.Iterable = None) -> None:
        data = list()

        # Do this as sets have a lower time complexity for lookups, so this will
        # be exponentially more efficient for large datasets.
        hashed_unordered_data = set()

        for item in iterable:
            if item not in hashed_unordered_data:
                data.append(item)
                hashed_unordered_data.add(item)

        self._data = tuple(data)
        del data, hashed_unordered_data

    def __contains__(self, x: SetType) -> bool:
        """Return true if the given object is present in the set."""
        return x in self._data

    def __len__(self) -> int:
        """Get the length of the set."""
        return len(self._data)

    def __iter__(self) -> typing.Iterator[SetType]:
        """Return an iterator across the set."""
        return iter(self._data)

    def __getitem__(self, index: int) -> SetType:
        """Access the element at the given index in the set."""
        return self._data[index]

    def __str__(self) -> str:
        """Get the string representation of the set."""
        return f'{{{",".join(repr(k) for k in self)}}}'

    __repr__ = __str__


class MutableOrderedSet(typing.AbstractSet, typing.Generic[SetType]):
    """
    A set data-type that maintains insertion order. This implementation is mutable.

    This is implemented as a valueless ordered dict underneath, and thus
    time complexities should match that implementation.

    Any implementation here should match the implementation of the Python Set type.
    """

    def __init__(self, iterable: typing.Iterable = None) -> None:
        # This implementation is just a dictionary that only utilises the keys.
        if iterable:
            self._dict = OrderedDict({k: None for k in iterable})
        else:
            self._dict = OrderedDict()

    def __contains__(self, x: SetType) -> bool:
        """Return true if the given object is present in the set."""
        return x in self._dict

    def __len__(self) -> int:
        """Get the length of the set."""
        return len(self._dict)

    def __iter__(self) -> typing.Iterator[SetType]:
        """Return an iterator across the set."""
        return iter(self._dict)

    def __getitem__(self, index: int) -> SetType:
        """Access the element at the given index in the set."""
        return list(self._dict.keys())[index]

    def __str__(self) -> str:
        """Get the string representation of the set."""
        return f'{{{",".join(repr(k) for k in self)}}}'

    __repr__ = __str__

    def add(self, x: SetType) -> None:
        """Adds a new element to the set."""
        self._dict[x] = None

    def discard(self, x: SetType) -> None:
        """Removes an element from the set."""
        self._dict.pop(x)


class TwoWayDict(OrderedDict):
    """
    A map that supports being reversed, and caches it's value to speed up
    reversal whilst maintaining some level of integrity.

    Note that value types that are iterable will be reversed in a way that
    enforces each value in the list is a separate key.

    To comply with Python3.7, this is Ordered by default.

    This inherits ``OrderedDict``, so will have all the members that ``dict``
    provides. In addition, the ``reversed()`` builtin can be used to obtain
    a reversed representation of the dict. 

    .. warning::
        This reversed representation is only valid for the duration of the
        internal cache. Any mutation operation to this original object will
        result in the cache being cleared. Thus, internal representations
        are considered to be snapshots.

    Example::

        >>> d = TwoWayDict({12: '12', 'bar': [1, 2, 3]})
        >>> reversed(d)
        {'12': 12, 1: 'bar', 2: 'bar', 3: 'bar'}

    """

    @cached_property()
    def _reversed_representation(self) -> dict:
        rev = OrderedDict()

        for k, v in self.items():
            if hasattr(v, "__iter__") and not isinstance(v, str):
                for sv in v:
                    rev[sv] = k
            else:
                rev[v] = k
        return rev

    def __reversed__(self) -> dict:
        return self._reversed_representation

    def __setitem__(self, key, value):
        if "_reversed_representation" in self.__dict__:
            del self.__dict__["_reversed_representation"]
        return super().__setitem__(key, value)


ObservableAsyncQueueType = typing.TypeVar("QueueType")


class ObservableAsyncQueue(asyncio.Queue, typing.Generic[ObservableAsyncQueueType]):
    """
    Override of an asyncio queue to provide a way of safely viewing the
    queue contents non-asynchronously using shallow copies.

    This is a really bad implementation. Probably will write a less crappy one in the
    future when I feel like it.
    """

    @cached_property()
    def view(self) -> deque:
        return self._queue.copy()

    def _put(self, item):
        super()._put(item)

        # Maybe invalidate the cache if there is one.
        if "view" in self.__dict__:
            del self.__dict__["view"]

        return item

    def _get(self):
        item = super()._get()

        # Maybe invalidate the cache if there is one.
        if "view" in self.__dict__:
            del self.__dict__["view"]

        return item

    def clear(self) -> None:
        """
        Clears the queue immediately without notifying any waiters. They will
        continue as they were.
        """
        self._queue.clear()

    async def get(self) -> ObservableAsyncQueueType:
        """
        Get from the queue.
        """
        return await super().get()

    async def put(self, item: ObservableAsyncQueueType) -> None:
        """
        Put onto the queue.
        """
        return await super().put(item)

    def __getitem__(self, item) -> ObservableAsyncQueueType:
        return self.view[item]

    def __setitem__(self, _, __):
        raise NotImplementedError("Please use the put coroutine.")

    def __str__(self):
        return str(self.view)

    def __len__(self) -> int:
        return self.qsize()

    def __iter__(self):
        """
        Returns an iterator across the current queue state at the time of calling.

        This will not be updated with the cache.
        """
        view = self.view
        return iter(view)

    def __contains__(self, item: object) -> bool:
        """
        Checks if the item is in this object at the current point in time.

        This shouldn't be updated with the cache, so should be deterministic.
        :param item: the item to look for.
        """
        return item in self.view

    async def unshift(self, item: ObservableAsyncQueueType):
        """
        Unshifts to the queue and notify listeners that a new item is available.
        """
        while self.full():
            putter = self._loop.create_future()
            self._putters.append(putter)
            try:
                await putter
            except Exception:
                putter.cancel()  # Just in case putter is not done yet.
                try:
                    # Clean self._putters from canceled putters.
                    self._putters.remove(putter)
                except ValueError:
                    # The putter could be removed from self._putters by a
                    # previous get_nowait call.
                    pass
                if not self.full() and not putter.cancelled():
                    # We were woken up by get_nowait(), but can't take
                    # the call.  Wake up the next in line.
                    self._wakeup_next(self._putters)
                raise

        self._queue.appendleft(item)

        if "view" in self.__dict__:
            del self.__dict__["view"]

        return item

    async def pop(self):
        """
        Pops the last item from the queue.
        """
        item = self._queue.pop()
        if "view" in self.__dict__:
            del self.__dict__["view"]

        return item


ValueT = typing.TypeVar("ValueT")


class ImmutableProxy(typing.Mapping):
    """
    An immutable proxy class. Similar to the Proxy class, but works differently.
    
    This is designed to be used for configuration files to convert them to dot-notation
    friendly immutable notation. It is recursive, and will convert list objects to
    tuples, dicts to instances of this class, and protects from recursive lookup issues.
    """

    def __init__(self, kwargs, *, recurse=True):
        """
        If recurse is True, it converts all inner dicts to this type too.
        """
        if not isinstance(kwargs, dict):
            raise TypeError(f"Expected dictionary, got {type(kwargs).__name__}")

        if recurse:
            self.__dict = self._recurse_replace(kwargs)
        else:
            self.__dict = kwargs

    def __getattr__(self, item):
        try:
            return self.__dict[item]
        except KeyError:
            raise AttributeError(item) from None

    def __getitem__(self, item):
        return self.__dict[item]

    def __len__(self) -> int:
        return len(self.__dict)

    def __iter__(self) -> typing.Iterator:
        return iter(self.__dict)

    def __str__(self):
        return str(self.__dict)

    def __repr__(self):
        return repr(self.__dict)

    def __hash__(self):
        return object.__hash__(self)

    @classmethod
    def _recurse_replace(cls, obj, already_passed=None):
        if already_passed is None:
            already_passed = []

        new_dict = {}
        for k, v in obj.items():
            if isinstance(v, dict):
                if v in already_passed:
                    new_dict[k] = v
                else:
                    already_passed.append(v)
                    new_dict[k] = cls._recurse_replace(v, already_passed)
            elif isinstance(v, list):
                new_dict[k] = tuple(v)
            else:
                new_dict[k] = v

        return cls(new_dict, recurse=False)


# noinspection PyAbstractClass
class Proxy(types.SimpleNamespace, typing.MutableMapping):
    """
    Special type of dict that internally is rewrired to allow dot-notation
    to access internal members. As a result all keys must be strings to be accessible::

        >>> p = Proxy(foo=10, bar=16)
        >>> p['foo']
        16
        >>> p.foo
        16
        >>> vars(p)
        {'foo': 10, 'bar': 16}

    This works using a special case of :class:`types.SimpleNamespace`.
    """

    # noinspection PyMissingConstructor
    def __init__(self, from_keys: dict = None, **kwargs):
        from_keys = from_keys or {}
        from_keys.update(**kwargs)
        super().__init__(**from_keys)

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __delitem__(self, item):
        delattr(self, item)

    def keys(self):
        return self.__dict__.keys()

    def __len__(self):
        return len(self.__dict__)

    def __iter__(self):
        return iter(self.__dict__)


class TypeSet(set):
    """
    A set for polymorphic types. This is a normal set that should take a 
    collection of classes/types. We can then use it like a normal frozenset, 
    except for one caveat: the ``in`` operator will also compare derived classes.
    
    Take the following example::
    
        >>> class Base:
        ...     ...
        
        >>> class Derived(Base):
        ...     ...
        
        >>> class NotDerived:
        ...     ...
        
        >>> ts = TypeSet({Base, str, int})
        
        >>> Base in ts
        True
        >>> Derived in ts
        True
        >>> str in ts
        True
        >>> NotDerived in ts
        False
        >>> ts
        {<class "Base">, <class "int">, <class "str">}
        
    Warning:
        Adding types that do not derive from the :class:`type` metaclass will
        result in a :class:`TypeError`.
    """

    def __init__(self, items=None):
        super().__init__()
        for item in items:
            self.add(item)

    def add(self, item) -> None:
        if not isinstance(item, type):
            raise TypeError("All members of a TypeSet must derive from type.")
        else:
            super().add(item)

    def __contains__(self, item) -> bool:
        for contained_item in iter(self):
            if issubclass(item, contained_item):
                return True
        return False


Regex = type(re.compile(r""))


class PatternSet(set):
    """
    Implements a set of patterns. These can be strings or regular expressions.

    Takes zero or more regex objects or strings to match.

    Parameters:
        case_insensitive:
            Defaults to False. If True, then strings and regular expressions unless
            given flags saying otherwise, will default to not matching on variadic
            case. For example, if False, ``hello`` would not match ``HeLlO``.
    """

    def __init__(self, *args, case_insensitive=False):
        super().__init__()

        class SearchableString(str):
            """Wrapper for a string that has a search method."""

            @property
            def pattern(self):
                return str(self)

            if case_insensitive:

                def search(self, other: str):
                    return other.lower().find(self.lower()) != -1

            else:

                def search(self, other: str):
                    return other.find(self) != -1

        self.__searchable_string = SearchableString
        self.__case_insensitive = case_insensitive

        for arg in args:
            self.add(arg)

    def add_str(self, value: str):
        """Adds a given string to the set."""
        return self.add(value)

    def add_regex(self, pattern, flags=...):
        if flags is ...:
            flags = re.I if self.__case_insensitive else 0

        regex = re.compile(pattern, flags)
        return self.add(regex)

    def add(self, value):
        # noinspection PyTypeChecker
        if isinstance(value, (str, int, bool, float, type(None))):
            value = self.__searchable_string(value)

        if isinstance(value, (self.__searchable_string, Regex)):
            return super().add(value)
        else:
            raise TypeError(f"Expected str or regex object, got {type(value).__name__}")

    def __contains__(self, item):
        for patt in self:
            s = patt.search(item)
            if s:
                return True
        return False

    def __eq__(self, other):
        return all(other_el in self for other_el in other)

    def __str__(self):
        return ", ".join(str(pat.pattern) for pat in self)
