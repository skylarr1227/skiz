#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import unittest

import asynctest

from libneko import aggregates


class OrderedSetTest(unittest.TestCase):
    def test_frozen_ordered_set(self):
        in_data = [10, 9, 9, 10, 8, 5, 4, 7, 6, 3, 1, 0, 10, 10, 4]
        out_data = [10, 9, 8, 5, 4, 7, 6, 3, 1, 0]
        fos = aggregates.FrozenOrderedSet(in_data)
        result = list(fos)
        self.assertEqual(out_data, result)

    def test_mutable_ordered_set(self):
        in_data = [10, 9, 9, 10, 8, 5, 4, 7, 6, 3, 1, 0, 10, 10, 4]
        out_data = [10, 9, 8, 5, 4, 7, 6, 3, 1, 0]
        fos = aggregates.FrozenOrderedSet(in_data)
        result = list(fos)
        self.assertEqual(out_data, result)


class ProxyTest(unittest.TestCase):
    def test_init_dict(self):
        proxy = aggregates.TwoWayDict({12: "12", "bar": [1, 2, 3]})
        test = {12: "12", "bar": [1, 2, 3]}
        self.assertCountEqual(proxy, test)
        self.assertDictEqual(proxy, test)

    def test_init_kwargs(self):
        proxy = aggregates.TwoWayDict(foo="12", bar=[1, 2, 3])
        test = {"bar": [1, 2, 3], "foo": "12"}
        self.assertCountEqual(proxy, test)
        self.assertDictEqual(proxy, test)

    def test_get_item(self):
        proxy = aggregates.TwoWayDict({12: "12", "bar": [1, 2, 3]})
        self.assertEqual("12", proxy[12])
        self.assertEqual([1, 2, 3], proxy["bar"])

        with self.assertRaises(KeyError):
            _ = proxy["lol"]

    def test_set_item(self):
        proxy = aggregates.TwoWayDict({12: "12", "bar": [1, 2, 3]})

        proxy["foo"] = 13
        proxy["bar"] = 14

        self.assertEqual("12", proxy[12])
        self.assertEqual(13, proxy["foo"])
        self.assertEqual(14, proxy["bar"])

    def test_del_item(self):
        proxy = aggregates.TwoWayDict({12: "12", "bar": [1, 2, 3]})
        del proxy[12]
        with self.assertRaises(KeyError):
            _ = proxy[12]
        del proxy["bar"]
        with self.assertRaises(KeyError):
            _ = proxy["bar"]

    def test_keys(self):
        proxy = aggregates.TwoWayDict({12: "12", "bar": [1, 2, 3]})
        self.assertIn(12, proxy.keys())
        self.assertIn("bar", proxy.keys())
        self.assertNotIn("potato", proxy.keys())

    def test_iter(self):
        proxy = aggregates.TwoWayDict({12: "12", "bar": [1, 2, 3]})
        i = iter(proxy)
        li = list(i)
        self.assertIn(12, li)
        self.assertIn("bar", li)
        self.assertNotIn("potato", li)


class TwoWayDictTest(unittest.TestCase):
    def test_reversal(self):
        twd = aggregates.TwoWayDict({12: "12", "bar": [1, 2, 3]})
        dwt = reversed(twd)
        self.assertDictEqual({"12": 12, 1: "bar", 2: "bar", 3: "bar"}, dwt)

    def test_cache_gets_cached_and_then_uncached(self):
        twd = aggregates.TwoWayDict({12: "12", "bar": [1, 2, 3]})

        cached = reversed(twd)
        cached2 = reversed(twd)
        self.assertIs(cached, cached2)

        # Uncache
        twd["xyz"] = ...

        cached3 = reversed(twd)
        self.assertIsNot(cached, cached3)


class ObservableAsyncQueueTest(asynctest.TestCase):
    async def test_view_is_shallow_copy(self):
        oaq = aggregates.ObservableAsyncQueue()
        await oaq.put("9")
        await oaq.put("18")
        await oaq.put("27")
        await oaq.put("36")

        view = oaq.view
        self.assertListEqual(list(view), list(oaq._queue))
        self.assertEqual(view, oaq._queue)
        self.assertIsNot(view, oaq._queue)

        # Shallow copy should use the same inner refs. If they are not equal though,
        # we know that the order is messed up or items are not copied over right, as opposed
        # to it being a messed up shallow-copy issue.
        self.assertEqual(list(view)[2], list(oaq._queue)[2])
        self.assertIs(list(view)[2], list(oaq._queue)[2])

    async def test_putter_does_uncache(self):
        oaq = aggregates.ObservableAsyncQueue()
        await oaq.put("9")
        await oaq.put("18")
        await oaq.put("27")
        await oaq.put("36")
        view1 = oaq.view
        await oaq.put("45")
        view2 = oaq.view
        self.assertNotEqual(view1, view2)

    async def test_getter_does_cache(self):
        oaq = aggregates.ObservableAsyncQueue()
        await oaq.put("9")
        await oaq.put("18")
        await oaq.put("27")
        await oaq.put("36")
        view1 = oaq.view
        view2 = oaq.view
        self.assertIs(view1, view2)

    async def test_getitem_uses_view(self):
        oaq = aggregates.ObservableAsyncQueue()
        await oaq.put("9")
        await oaq.put("18")
        await oaq.put("27")
        await oaq.put("36")

        view = oaq.view
        view.append("0")

        self.assertEqual("0", oaq[4])

    async def test_unshift_works(self):
        oaq = aggregates.ObservableAsyncQueue()
        await oaq.put("9")
        await oaq.put("18")
        await oaq.put("27")
        await oaq.put("36")

        await oaq.unshift("0")
        self.assertListEqual(["0", "9", "18", "27", "36"], list(oaq.view))

    async def test_pop_works(self):
        oaq = aggregates.ObservableAsyncQueue()
        await oaq.put("9")
        await oaq.put("18")
        await oaq.put("27")
        await oaq.put("36")

        self.assertEqual("36", await oaq.pop())
        self.assertEqual("27", await oaq.pop())
        self.assertEqual("18", await oaq.pop())
        self.assertEqual("9", await oaq.pop())

        with self.assertRaises(IndexError):
            await oaq.pop()


class TypeSetTest(unittest.TestCase):
    def test_same_type(self):
        ts = aggregates.TypeSet({int, str, float})
        self.assertIn(str, ts)
        self.assertIn(int, ts)
        self.assertIn(float, ts)
        self.assertNotIn(list, ts)
        self.assertNotIn(object, ts)

    def test_polymorphic_type(self):
        ts = aggregates.TypeSet({object})
        self.assertIn(str, ts)
        self.assertIn(int, ts)
        self.assertIn(float, ts)
        self.assertIn(list, ts)
        self.assertIn(object, ts)

    def test_invalid_member_1(self):
        with self.assertRaises(TypeError):
            aggregates.TypeSet({object()})

    def test_invalid_member_2(self):
        ts = aggregates.TypeSet({})

        with self.assertRaises(TypeError):
            ts.add(object())


class PatternSetTest(unittest.TestCase):
    def test_string_pattern_match(self):
        ps = aggregates.PatternSet("hello", "HELLO")
        self.assertIn("hello", ps)
        self.assertIn("hellohello", ps)
        self.assertIn("hello hello", ps)
        self.assertIn("HELLO", ps)
        self.assertNotIn("lo", ps)
        self.assertNotIn("heLlO", ps)

    def test_regex_pattern_match(self):
        ps = aggregates.PatternSet(re.compile(r"\bhello\b"), re.compile("<.*?>"))
        self.assertIn("he said hello world", ps)
        self.assertNotIn("he said HELLO world", ps)
        self.assertNotIn("pOtAto", ps)
        self.assertIn('<html><body><h1 class="foobar">Hello, World</h1></body></html>', ps)

    def test_regex_pattern_match_using_add_regex_method(self):
        ps = aggregates.PatternSet()
        ps.add_regex(r"\bhello\b")
        ps.add_regex(r"<.*?>")
        self.assertIn("he said hello world", ps)
        self.assertNotIn("he said HELLO world", ps)
        self.assertNotIn("pOtAto", ps)
        self.assertIn('<html><body><h1 class="foobar">Hello, World</h1></body></html>', ps)

    def test_string_pattern_match_case_insensitive(self):
        ps = aggregates.PatternSet("hello", "HELLO", case_insensitive=1)
        self.assertIn("hello", ps)
        self.assertIn("hellohello", ps)
        self.assertIn("hello hello", ps)
        self.assertIn("HELLO", ps)
        self.assertNotIn("lo", ps)
        self.assertIn("heLlO", ps)

    def test_regex_pattern_match_case_insensitive(self):
        ps = aggregates.PatternSet(case_insensitive=1)
        ps.add_regex(r"\bhello\b")
        ps.add_regex(r"<.*?>")
        self.assertIn("he said hello world", ps)
        self.assertIn("he said HELLO world", ps)
        self.assertNotIn("pOtAto", ps)
        self.assertIn('<html><body><h1 class="foobar">Hello, World</h1></body></html>', ps)
