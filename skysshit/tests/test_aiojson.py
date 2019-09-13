#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests aiofiles and aiojson integration.
"""
import json
import shutil

import asynctest
from libneko import aiojson, filesystem


test_data_obj = {"foo": [1, "bar", None], "baz": False, "bork": {}}

test_data_raw = json.dumps(test_data_obj)

test_file = ".test.json"


class AioJsonTest(asynctest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(test_file, ignore_errors=True)

    async def test_aiodump(self):
        async with filesystem.aioopen(test_file, "w") as fp:
            await aiojson.aiodump(test_data_obj, fp)

        with open(test_file) as fp:
            data = fp.read()
            self.assertEqual(test_data_raw, data)

    async def test_aioload(self):
        with open(test_file, "w") as fp:
            fp.write(test_data_raw)

        async with filesystem.aioopen(test_file) as fp:
            obj = await aiojson.aioload(fp)

        self.assertEqual(test_data_obj, obj)
