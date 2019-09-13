#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest

from libneko import strings


class JoinTest(asynctest.TestCase):
    def test_join_list(self):
        items = ["foo", "bar", "baz", "bork"]
        expected = "foo, bar, baz, bork"
        joined = strings.join(", ", items)
        self.assertEqual(expected, joined)

    def test_join_repr(self):
        class Reprify(str):
            def __init__(self, string):
                self.string = string

            def __str__(self):
                return self.string

            def __repr__(self):
                return "sausage"

        items = [*map(Reprify, ["foo", "bar", "baz", "bork"])]
        expected = "sausage, sausage, sausage, sausage"
        joined = strings.join(", ", items, cast=repr)
        self.assertEqual(expected, joined)

    def test_join_non_list_type(self):
        items = reversed(["foo", "bar", "baz", "bork"])
        expected = "bork, baz, bar, foo"
        joined = strings.join(", ", items)
        self.assertEqual(expected, joined)


class SensitiveStrTest(asynctest.TestCase):
    def test_sensitive_init(self):
        shh = strings.SensitiveStr("hello, world")
        self.assertEqual("hello, world", shh)

    def test_sensitive_cast(self):
        shh = strings.SensitiveStr("shh")
        self.assertNotEqual("shh", str(shh))
        self.assertNotEqual("shh", repr(shh))
        shhhhh = strings.SensitiveStr("ahh")
        self.assertEqual(str(shh), str(shhhhh))
        self.assertEqual(repr(shh), repr(shhhhh))

    def test_unmask(self):
        shh = strings.SensitiveStr("shh")
        self.assertEqual("shh", shh())


class CapTest(asynctest.TestCase):
    def test_cap_start(self):
        in_data = "test"
        out_data = "Test"
        result = strings.cap_start(in_data)
        self.assertEqual(out_data, result)


class CamelCaseTest(asynctest.TestCase):
    def test_camelcase_prettify(self):
        in_data = "LoremIpsumDolorSitAmet"
        out_data = "Lorem ipsum dolor sit amet"
        result = strings.camelcase_prettify(in_data)
        self.assertEqual(out_data, result)


class FormatSecondsTest(asynctest.TestCase):
    def test_format_seconds_precision(self):
        from datetime import timedelta

        MONTHS = 3
        DAYS = 1
        MINUTES = 14
        SECONDS = 33

        td = timedelta(days=MONTHS * 30 + DAYS, seconds=MINUTES * 60 + SECONDS)
        string = strings.format_seconds(td.total_seconds(), precision=3)
        expected = f"{MONTHS} months, {DAYS} day, {MINUTES} minutes"
        self.assertEqual(expected, string)

    def test_format_seconds_no_precision(self):
        from datetime import timedelta

        MONTHS = 3
        DAYS = 1
        MINUTES = 14
        SECONDS = 33

        td = timedelta(days=MONTHS * 30 + DAYS, seconds=MINUTES * 60 + SECONDS)
        string = strings.format_seconds(td.total_seconds())
        expected = f"{MONTHS} months, {DAYS} day, {MINUTES} minutes, {SECONDS} seconds"
        self.assertEqual(expected, string)


class PrettyListTest(asynctest.TestCase):
    def test_pretty_list_sync(self):
        in_data = [["abc", "cba", "bca"], "\n"]
        out_data = "abc\ncba\nbca"
        result = strings.pretty_list(in_data[0], sep=in_data[1])
        self.assertEqual(out_data, result)

    async def test_pretty_list_async(self):
        class AsyncIterable:
            def __init__(self, list):
                self.list = list

            def __aiter__(self):
                return self

            async def __anext__(self):
                try:
                    return self.list.pop(0)
                except IndexError:
                    raise StopAsyncIteration from None

        in_data = [["abc", "cba", "bca"], "\n"]
        out_data = "abc\ncba\nbca"
        result = await strings.pretty_list(AsyncIterable(in_data[0]), sep=in_data[1])
        self.assertEqual(out_data, result)
