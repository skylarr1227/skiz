#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio

import asynctest
import libneko


class PropertyTest(asynctest.TestCase):
    def test_read_only_property(self):
        class Klass1:
            @libneko.properties.read_only_property
            def foo(self):
                return 22

        k = Klass1()
        self.assertEqual(22, k.foo)

        with self.assertRaises(Exception):

            class Klass2:
                @libneko.properties.read_only_property
                def foo(self):
                    return 22

                @libneko.setter
                def foo(self, value):
                    self.value = 22

            k = Klass2()

    def test_read_only_class_property(self):
        class Klass1:
            @libneko.properties.read_only_class_property
            def foo(cls):
                return 22

        k = Klass1()
        self.assertEqual(22, k.foo)
        self.assertEqual(22, Klass1.foo)

        with self.assertRaises(Exception):

            class Klass2:
                @libneko.properties.read_only_class_property
                def foo(cls):
                    return 22

                @libneko.setter
                def foo(cls, value):
                    self.value = 22

            k = Klass2()

    def test_instance_cached_property(self):
        class Klass:
            counter = 0

            @libneko.properties.InstanceCachedProperty
            def foo(self):
                self.counter += 1
                return self.counter

        k = Klass()

        self.assertEqual(1, k.foo)
        self.assertEqual(1, k.foo)
        self.assertEqual(1, k.counter)

        del k.foo

        self.assertEqual(2, k.foo)
        self.assertEqual(2, k.foo)
        self.assertEqual(2, k.counter)

    def test_slotted_instance_cached_property(self):
        class Klass:
            __slots__ = ("counter", libneko.properties.SLOTTED_PREFIX + "foo")

            def __init__(self):
                self.counter = 0

            @libneko.properties.SlottedCachedProperty
            def foo(self):
                self.counter += 1
                return self.counter

        k = Klass()

        self.assertEqual(1, k.foo)
        self.assertEqual(1, k.foo)
        self.assertEqual(1, k.counter)

        del k.foo

        self.assertEqual(2, k.foo)
        self.assertEqual(2, k.foo)
        self.assertEqual(2, k.counter)

    async def test_async_instance_cached_property(self):
        class Klass:
            counter = 0

            @libneko.properties.AsyncCachedProperty
            @asyncio.coroutine
            def foo(self):
                self.counter += 1
                return self.counter

        k = Klass()

        self.assertEqual(1, await k.foo)
        self.assertEqual(1, await k.foo)
        self.assertEqual(1, k.counter)

        del k.foo

        self.assertEqual(2, await k.foo)
        self.assertEqual(2, await k.foo)
        self.assertEqual(2, k.counter)

    async def test_async_slotted_instance_cached_property(self):
        class Klass:
            __slots__ = ("counter", libneko.properties.SLOTTED_PREFIX + "foo")

            def __init__(self):
                self.counter = 0

            @libneko.properties.AsyncSlottedCachedProperty
            async def foo(self):
                self.counter += 1
                return self.counter

        k = Klass()

        self.assertEqual(1, await k.foo)
        self.assertEqual(1, await k.foo)
        self.assertEqual(1, k.counter)

        del k.foo

        self.assertEqual(2, await k.foo)
        self.assertEqual(2, await k.foo)
        self.assertEqual(2, k.counter)
