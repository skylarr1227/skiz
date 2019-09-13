#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import traceback
import warnings

import aiohttp
import asyncio
import atexit
import io
import logging
import sys
import unittest

sys.argv.append("discover")


class IOProxy:
    def __init__(self):
        self.stringio = io.StringIO()

    def __getattr__(self, item):
        return getattr(self.stringio, item)


log_stream = IOProxy()


class EventLoopPolicy(asyncio.AbstractEventLoopPolicy):
    def __init__(self):
        self.inner_policy = asyncio.DefaultEventLoopPolicy()

    def get_event_loop(self):
        loop = self.inner_policy.get_event_loop()
        logging.info("Getting event loop %s", loop)
        return loop

    def set_event_loop(self, loop):
        logging.info("Changing event loop to %s", loop)
        return self.inner_policy.set_event_loop(loop)

    def new_event_loop(self):
        loop = self.inner_policy.new_event_loop()
        loop.set_debug(True)
        logging.info("Created new event loop %s", loop)
        return loop

    def get_child_watcher(self):
        logging.info("Accessing child watcher")
        return self.inner_policy.get_child_watcher()

    def set_child_watcher(self, watcher):
        logging.info("Setting child watcher to %s", watcher)
        return self.inner_policy.set_child_watcher(watcher)


asyncio.set_event_loop_policy(EventLoopPolicy())


logging.basicConfig(
    level="DEBUG",
    stream=log_stream,
    format="\033[2;3;37m 🗩 %(relativeCreated)d ms %(levelname)s %(name)s -- %(message)s \033[0m",
)

logging.root.name = "libneko"

results: unittest.TextTestResult = None

with warnings.catch_warnings(record=True):
    # Capture any asyncio aiohttp client sessions so we can close them
    _ClientSession = aiohttp.ClientSession

    class ClientSession(_ClientSession):
        _open_sessions = []

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            type(self)._open_sessions.append(self)

        async def close(self):
            try:
                type(self)._open_sessions.remove(self)
            finally:
                return await _ClientSession.close(self)

    # Mixin!
    aiohttp.ClientSession = ClientSession


@atexit.register
def die():
    global results
    if asyncio.get_event_loop().is_closed():
        loop = asyncio.new_event_loop()
    else:
        loop = asyncio.get_event_loop()

    async def closer():
        for session in ClientSession._open_sessions:
            await session.close()

    loop.run_until_complete(closer())
    loop.close()


class LogCollectionResultKlazz(unittest.TextTestResult):
    def __enter__(self):
        log_stream.stringio = io.StringIO()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stderr.write(log_stream.getvalue())
        if exc_val:
            traceback.print_exception(exc_type, exc_val, exc_tb)

    def startTest(self, test):
        self.__ctx = self.__enter__()
        super().startTest(test)

    def stopTest(self, test):
        self.__ctx.__exit__(*sys.exc_info())
        sys.exc_value = None
        sys.exc_traceback = None
        del self.__ctx


loader = unittest.TestLoader()
suite = loader.discover("libneko.test", pattern="__init__.py")
suite.addTests(loader.discover("libneko.test"))
runner = unittest.TextTestRunner(verbosity=5, resultclass=LogCollectionResultKlazz)
# noinspection PyRedeclaration
results = runner.run(suite)

if results.failures:
    exit(1)  # Cause CI to fall over.
else:
    exit(0)
