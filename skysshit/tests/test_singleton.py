#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest

from libneko import singleton


class SingletonTest(unittest.TestCase):
    def test_singleton(self):
        class SomeClass(singleton.Singleton):
            pass

        obj1 = SomeClass()
        obj2 = SomeClass()
        obj3 = SomeClass()

        self.assertIs(obj1, obj2)
        self.assertIs(obj1, obj3)
        self.assertIs(obj2, obj3)
