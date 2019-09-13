#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Here be dragons.
"""
import functools
import inspect
import warnings

import asynctest
import asyncio

from libneko import funcmods


class EnsureCoroutineTest(asynctest.TestCase):
    async def test_ensure_coroutine(self):
        @funcmods.ensure_coroutine_function
        def not_a_coroutine(a, b):
            return a + b

        @funcmods.ensure_coroutine_function
        async def definitely_a_coroutine(a, b):
            return a + b

        self.assertEqual(27, await not_a_coroutine(9, 18))
        self.assertEqual(36, await definitely_a_coroutine(9, 27))


class SignatureTest(asynctest.TestCase):
    def test_steal_signature_from_def(self):
        def first_source(a: int, b: str, c) -> "ayyy lmao":
            pass

        @funcmods.steal_signature_from(first_source)
        def first_target():
            pass

        sentinel = object()

        self.assertEqual(
            inspect.signature(first_source), getattr(first_target, "__signature__", sentinel)
        )

    def test_steal_signature_from_async_def(self):
        async def first_source(a: int, b: str, c) -> "ayyy lmao":
            pass

        @funcmods.steal_signature_from(first_source)
        def first_target():
            pass

        sentinel = object()

        self.assertEqual(
            inspect.signature(first_source), getattr(first_target, "__signature__", sentinel)
        )

    def test_steal_docstring_in_signature_stealing(self):
        async def first_source(a: int, b: str, c) -> "ayyy lmao":
            """Secret message"""
            pass

        @funcmods.steal_signature_from(first_source, steal_docstring=True)
        def first_target():
            """Lol"""
            pass

        self.assertIsNotNone(inspect.getdoc(first_source))
        self.assertIn(inspect.getdoc(first_source), inspect.getdoc(first_target))

    def test_steal_docstring_replace(self):
        async def first_source(a: int, b: str, c) -> "ayyy lmao":
            """Secret message"""
            pass

        @funcmods.steal_docstring_from(first_source, mode="replace")
        def first_target():
            """Lol"""
            pass

        self.assertEqual(inspect.getdoc(first_source), inspect.getdoc(first_target))

    def test_steal_docstring_append(self):
        async def first_source(a: int, b: str, c) -> "ayyy lmao":
            """Secret message"""
            pass

        @funcmods.steal_docstring_from(first_source, mode="append")
        def first_target():
            """Lol"""
            pass

        src = inspect.getdoc(first_source)
        tgt = inspect.getdoc(first_target)
        self.assertTrue(tgt.startswith(src), f"{tgt!r} doesn't start with {src!r}")

    def test_steal_docstring_prepend(self):
        async def first_source(a: int, b: str, c) -> "ayyy lmao":
            """Secret message"""
            pass

        @funcmods.steal_docstring_from(first_source, mode="prepend")
        def first_target():
            """Lol"""
            pass

        src = inspect.getdoc(first_source)
        tgt = inspect.getdoc(first_target)
        self.assertTrue(tgt.endswith(src), f"{tgt!r} doesn't end with {src!r}")


def ignore_warnings(method):
    @functools.wraps(method)
    def call(*args, **kwargs):
        with warnings.catch_warnings(record=True):
            return method(*args, **kwargs)

    return call


class WrapsTest(asynctest.TestCase):
    def test_name(self):
        def foo():
            pass

        @funcmods.wraps(foo)
        def bar():
            pass

        self.assertEqual(foo.__name__, bar.__name__)

    def test_doc(self):
        def foo():
            """potato"""
            pass

        @funcmods.wraps(foo)
        def bar():
            """bacon"""
            pass

        self.assertEqual(inspect.getdoc(foo), inspect.getdoc(bar))

    def test_type_error(self):
        async def foo():
            pass

        with self.assertRaises(TypeError):
            """
            Should always raise a type error if we wrap a function with a coroutine, as it means it may never be
            awaited!
            """

            @funcmods.wraps(foo)
            def bar():
                pass


###
### Funcmods coroutine stuff that autogenerates unit tests kind of.
###


def function():
    pass


async def async_function():
    pass


async def async_generator():
    for i in range(10):
        yield i


@asyncio.coroutine
def coroutine_function():
    pass


@asyncio.coroutine
def coroutine_generator():
    for i in range(10):
        yield i


lambda_expression_function = lambda: None


class Klass:
    def method(self):
        pass

    @staticmethod
    def static_method():
        pass

    @classmethod
    def class_method(cls):
        pass

    lambda_expression_method = lambda self: None

    @property
    def property_method(self):
        return getattr(Klass, "property_method")

    @property
    @asyncio.coroutine
    def coroutine_property_method(self):
        return getattr(Klass, "coroutine_property_method")

    @property
    async def async_property_method(self):
        return getattr(Klass, "async_property_method")

    async def async_function(self):
        pass

    async def async_generator(self):
        for i in range(10):
            yield i

    @asyncio.coroutine
    def coroutine_function(self):
        pass

    @asyncio.coroutine
    def coroutine_generator(self):
        for i in range(10):
            yield i


class CoroutineChecksTests(asynctest.TestCase):
    def _test(self, function, matrix):
        for expression, expected in matrix.items():
            if isinstance(expression, type):
                expr_str = f"{expression.__qualname__} type"
            elif hasattr(expression, "__qualname__"):
                expr_str = expression.__qualname__
            else:
                expr_str = f"{type(expression).__qualname__} object"

            expr_str += " " + str(expression)

            with self.subTest(f"{function.__qualname__}({expr_str})"):
                actual = function(expression)
                self.assertEqual(
                    expected, actual, f"{function}({expr_str}) := {actual} != expected {expected}"
                )

    @ignore_warnings
    def test_is_coroutine_function(self):
        obj = Klass()
        matrix = {
            function: False,
            async_function: True,
            async_function(): False,
            async_generator: False,
            async_generator(): False,
            coroutine_function: True,
            coroutine_function(): False,
            coroutine_generator: True,
            coroutine_generator(): False,
            # Class stuff
            obj.method: False,
            obj.async_function: True,
            obj.async_function(): False,
            obj.async_generator: False,
            obj.async_generator(): False,
            obj.coroutine_function: True,
            obj.coroutine_function(): False,
            obj.coroutine_generator: True,
            obj.coroutine_generator(): False,
            # Lambdas
            obj.lambda_expression_method: False,
            lambda_expression_function: False,
            # Property
            obj.property_method: False,
            obj.async_property_method: False,
            obj.coroutine_property_method: False,
            obj.static_method: False,
            obj.class_method: False,
            # Misc.
            None: False,
            1: False,
            tuple(): False,
            tuple: False,
        }
        self._test(funcmods.is_coroutine_function, matrix)

    @ignore_warnings
    def test_is_coroutine(self):
        obj = Klass()
        matrix = {
            function: False,
            async_function: False,
            async_function(): True,
            async_generator: False,
            async_generator(): False,
            coroutine_function: False,
            coroutine_function(): True,
            coroutine_generator: False,
            coroutine_generator(): True,
            # Class stuff
            obj.method: False,
            obj.async_function: False,
            obj.async_function(): True,
            obj.async_generator: False,
            obj.async_generator(): False,
            obj.coroutine_function: False,
            obj.coroutine_function(): True,
            obj.coroutine_generator: False,
            obj.coroutine_generator(): True,
            # Lambdas
            obj.lambda_expression_method: False,
            lambda_expression_function: False,
            # Property
            obj.property_method: False,
            obj.async_property_method: True,
            obj.coroutine_property_method: True,
            obj.static_method: False,
            obj.class_method: False,
            # Misc.
            None: False,
            1: False,
            tuple(): False,
            tuple: False,
        }
        self._test(funcmods.is_coroutine, matrix)

    @ignore_warnings
    def test_is_async_def_function(self):
        obj = Klass()
        matrix = {
            function: False,
            async_function: True,
            async_function(): False,
            async_generator: False,
            async_generator(): False,
            coroutine_function: False,
            coroutine_function(): False,
            coroutine_generator: False,
            coroutine_generator(): False,
            # Class stuff
            obj.method: False,
            obj.async_function: True,
            obj.async_function(): False,
            obj.async_generator: False,
            obj.async_generator(): False,
            obj.coroutine_function: False,
            obj.coroutine_function(): False,
            obj.coroutine_generator: False,
            obj.coroutine_generator(): False,
            # Lambdas
            obj.lambda_expression_method: False,
            lambda_expression_function: False,
            # Property
            obj.property_method: False,
            obj.async_property_method: False,
            obj.coroutine_property_method: False,
            obj.static_method: False,
            obj.class_method: False,
            # Misc.
            None: False,
            1: False,
            tuple(): False,
            tuple: False,
        }
        self._test(funcmods.is_async_def_function, matrix)

    @ignore_warnings
    def test_is_async_def_coroutine(self):
        obj = Klass()
        matrix = {
            function: False,
            async_function: False,
            async_function(): True,
            async_generator: False,
            async_generator(): False,
            coroutine_function: False,
            coroutine_function(): False,
            coroutine_generator: False,
            coroutine_generator(): False,
            # Class stuff
            obj.method: False,
            obj.async_function: False,
            obj.async_function(): True,
            obj.async_generator: False,
            obj.async_generator(): False,
            obj.coroutine_function: False,
            obj.coroutine_function(): False,
            obj.coroutine_generator: False,
            obj.coroutine_generator(): False,
            # Lambdas
            obj.lambda_expression_method: False,
            lambda_expression_function: False,
            # Property
            obj.property_method: False,
            obj.async_property_method: True,
            obj.coroutine_property_method: False,
            obj.static_method: False,
            obj.class_method: False,
            # Misc.
            None: False,
            1: False,
            tuple(): False,
            tuple: False,
        }
        self._test(funcmods.is_async_def_coroutine, matrix)

    @ignore_warnings
    def test_is_generator_coroutine_function(self):
        obj = Klass()
        matrix = {
            function: False,
            async_function: False,
            async_function(): False,
            async_generator: False,
            async_generator(): False,
            coroutine_function: True,
            coroutine_function(): False,
            coroutine_generator: True,
            coroutine_generator(): False,
            # Class stuff
            obj.method: False,
            obj.async_function: False,
            obj.async_function(): False,
            obj.async_generator: False,
            obj.async_generator(): False,
            obj.coroutine_function: True,
            obj.coroutine_function(): False,
            obj.coroutine_generator: True,
            obj.coroutine_generator(): False,
            # Lambdas
            obj.lambda_expression_method: False,
            lambda_expression_function: False,
            # Property
            obj.property_method: False,
            obj.async_property_method: False,
            obj.coroutine_property_method: False,
            obj.static_method: False,
            obj.class_method: False,
            # Misc.
            None: False,
            1: False,
            tuple(): False,
            tuple: False,
        }
        self._test(funcmods.is_generator_coroutine_function, matrix)

    @ignore_warnings
    def test_is_generator_coroutine(self):
        obj = Klass()
        matrix = {
            function: False,
            async_function: False,
            async_function(): False,
            async_generator: False,
            async_generator(): False,
            coroutine_function: False,
            coroutine_function(): True,
            coroutine_generator: False,
            coroutine_generator(): True,
            # Class stuff
            obj.method: False,
            obj.async_function: False,
            obj.async_function(): False,
            obj.async_generator: False,
            obj.async_generator(): False,
            obj.coroutine_function: False,
            obj.coroutine_function(): True,
            obj.coroutine_generator: False,
            obj.coroutine_generator(): True,
            # Lambdas
            obj.lambda_expression_method: False,
            lambda_expression_function: False,
            # Property
            obj.property_method: False,
            obj.async_property_method: False,
            obj.coroutine_property_method: True,
            obj.static_method: False,
            obj.class_method: False,
            # Misc.
            None: False,
            1: False,
            tuple(): False,
            tuple: False,
        }
        self._test(funcmods.is_generator_coroutine, matrix)
