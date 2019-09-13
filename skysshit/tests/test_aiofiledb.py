#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests the crappy asyncio file-based database module.
"""
import asyncio
import json
import logging
import os

import asynctest

from libneko import aiofiledb


@asynctest.skipIf(os.getenv("SKIP_SLOW_TESTS", False), reason="User opted to skip slow tests.")
class AioFileDbTesterMixin:
    FILE_NAME = "test-db.json"
    ASSUME_NO_EXTERNAL_CHANGES: bool

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.FILE_NAME)

    def setUp(self):
        with open(self.FILE_NAME, "w") as fp:
            fp.write("{}")

    async def test_file_read(self):
        OBJECT = {
            "foo": 123,
            "bar": 456,
            "baz": "789",
            "bork": ["a", "b", "c", "d", 99, True, False, None, 2.17],
            "qux": {"lorem": "ipsum", "ayy": [1, 2, 3]},
            "quux": None,
        }

        with open(self.FILE_NAME, "w") as fp:
            json.dump(OBJECT, fp)

        db = aiofiledb.AsyncSimpleDatabase(
            self.FILE_NAME, expect_no_other_access=self.ASSUME_NO_EXTERNAL_CHANGES
        )
        await db.wait_for_ready()

        self.assertEqual(len(OBJECT), await db.size())
        db.close()

    async def test_file_write(self):
        OBJECT = {
            "foo": 123,
            "bar": 456,
            "baz": "789",
            "bork": ["a", "b", "c", "d", 99, True, False, None, 2.17],
            "qux": {"lorem": "ipsum", "ayy": [1, 2, 3]},
            "quux": None,
        }

        db = aiofiledb.AsyncSimpleDatabase(
            self.FILE_NAME, expect_no_other_access=self.ASSUME_NO_EXTERNAL_CHANGES
        )
        await db.wait_for_ready()

        for k, v in OBJECT.items():
            await db.set(k, v)

        with open(self.FILE_NAME) as fp:
            data = json.load(fp)

        self.assertEqual(len(OBJECT), len(data))
        db.close()

    async def test_no_deadlock_and_resolution_order(self):
        db = aiofiledb.AsyncSimpleDatabase(
            self.FILE_NAME, expect_no_other_access=self.ASSUME_NO_EXTERNAL_CHANGES
        )
        nonesy = await db.get_or_default("foo")
        await db.set("foo", 69),
        sixty_ninesy = await db.get_or_default("foo")

        self.assertIsNone(nonesy)
        self.assertEqual(69, sixty_ninesy)
        db.close()

    async def test_cache_at_intervals(self):

        sema4 = 0

        class Tester(aiofiledb.AsyncSimpleDatabase):  #
            async def write_to_disk(self):
                nonlocal sema4
                sema4 += 1
                await super().write_to_disk()

        PERIOD = 4
        db = Tester(
            self.FILE_NAME,
            cache_period=PERIOD,
            expect_no_other_access=self.ASSUME_NO_EXTERNAL_CHANGES,
        )
        await db.set("foo", 12321)
        await asyncio.sleep(PERIOD * 1.2)
        self.assertEqual(1, sema4)
        db.close()


class AioFileDbNoExternalAcccess(AioFileDbTesterMixin, asynctest.TestCase):
    ASSUME_NO_EXTERNAL_CHANGES = True


class AioFileDbExpectExternalAcccess(AioFileDbTesterMixin, asynctest.TestCase):
    ASSUME_NO_EXTERNAL_CHANGES = False
