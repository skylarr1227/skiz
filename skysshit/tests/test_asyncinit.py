#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest
from libneko import asyncinit


class AsyncInitTest(asynctest.TestCase):
    async def test_basic_async_init(self):
        # Ensures AsyncInit actually is called
        class AsyncInitInstance(asyncinit.AsyncInit):
            async def __ainit__(self, foo, bar, baz):
                self.foo = foo
                self.bar = bar
                self.baz = baz

        obj = await AsyncInitInstance(5, 10, 15)

        self.assertEqual(5, getattr(obj, "foo", object()))
        self.assertEqual(10, getattr(obj, "bar", object()))
        self.assertEqual(15, getattr(obj, "baz", object()))

    async def test_resolution_order(self):
        # Ensures init is called before async_init
        sema4 = 0

        class AsyncInitInstance(asyncinit.AsyncInit):
            def __init__(_):
                nonlocal sema4
                self.assertEqual(0, sema4)
                sema4 += 1

            async def __ainit__(_):
                nonlocal sema4
                self.assertEqual(1, sema4)
                sema4 += 1

        self.assertEqual(0, sema4)
        _ = await AsyncInitInstance()
        self.assertEqual(2, sema4)

    async def test_mro_propagation(self):
        """Test that all super init methods get invoked at some point."""

        class Foo:
            def __init__(self):
                self.it_worked = True

        class Bar(asyncinit.AsyncInit, Foo):
            def __init__(self):
                super().__init__()

            async def __ainit__(self):
                ...

        instance = await Bar()

        self.assertTrue(hasattr(instance, "it_worked"))
        self.assertEqual(True, instance.it_worked)
