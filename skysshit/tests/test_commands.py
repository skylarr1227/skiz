#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proves the fix for #35 which was the issue of libneko.Bot decorators for commands raising duplicated
kwargs errors.
"""
import asynctest

import libneko


class DefaultCommandKlassCogTest(asynctest.TestCase):
    PREFIX = "?"

    async def do_setUp(self):
        self.bot = libneko.Bot(command_prefix=self.PREFIX)

        @self.bot.command()
        async def root_command(self_, ctx):
            self.assertIsInstance(ctx, libneko.Context)
            self.assertFalse(self.sema4)
            self.assertIs(self, self_)
            self.sema4 = True

        @self.bot.group()
        async def root_group(self_, ctx):
            self.assertIsInstance(ctx, libneko.Context)
            self.assertFalse(self.sema4)
            self.assertIs(self, self_)
            self.sema4 = True

        @root_group.command()
        async def subcommand(self_, ctx):
            self.assertIsInstance(ctx, libneko.Context)
            self.assertFalse(self.sema4)
            self.assertIs(self, self_)
            self.sema4 = True

        @root_group.group()
        async def subgroup(self_, ctx):
            self.assertIsInstance(ctx, libneko.Context)
            self.assertFalse(self.sema4)
            self.assertIs(self, self_)
            self.sema4 = True

        self.root_command = root_command
        self.root_group = root_group
        self.subcommand = subcommand
        self.subgroup = subgroup

    async def mock_context(self):
        message = libneko.aggregates.Proxy(_state=None)
        return libneko.Context(message=message, prefix=self.PREFIX)

    async def mock_invoke(self, command):
        setattr(self, "sema4", False)
        await command.callback(self, await self.mock_context())
        self.assertTrue(getattr(self, "sema4"))

    async def test_call_default_command(self):
        await self.do_setUp()
        await self.mock_invoke(self.root_command)

    async def test_call_default_group(self):
        await self.do_setUp()
        await self.mock_invoke(self.root_group)

    async def test_call_default_command_subcommand(self):
        await self.do_setUp()
        await self.mock_invoke(self.subcommand)

    async def test_call_default_command_subgroup(self):
        await self.do_setUp()
        await self.mock_invoke(self.subgroup)


class OverriddenCommandKlassCogTest(asynctest.TestCase):
    PREFIX = "?"

    async def do_setUp(self):
        self.bot = libneko.Bot(command_prefix=self.PREFIX)

        class CustomCommandKlazz(libneko.Command):
            ...

        self.CustomCommandKlazz = CustomCommandKlazz

        class CustomGroupKlazz(libneko.Group):
            ...

        self.CustomGroupKlazz = CustomGroupKlazz

        @self.bot.command(cls=CustomCommandKlazz)
        async def root_command(self_, ctx):
            self.assertIsInstance(ctx, libneko.Context)
            self.assertFalse(self.sema4)
            self.assertIs(self, self_)
            self.sema4 = True

        @self.bot.group(cls=CustomGroupKlazz)
        async def root_group(self_, ctx):
            self.assertIsInstance(ctx, libneko.Context)
            self.assertFalse(self.sema4)
            self.assertIs(self, self_)
            self.sema4 = True

        @root_group.command(cls=CustomCommandKlazz)
        async def subcommand(self_, ctx):
            self.assertIsInstance(ctx, libneko.Context)
            self.assertFalse(self.sema4)
            self.assertIs(self, self_)
            self.sema4 = True

        @root_group.group(cls=CustomGroupKlazz)
        async def subgroup(self_, ctx):
            self.assertFalse(self.sema4)
            self.assertIs(self, self_)
            self.sema4 = True

        self.root_command = root_command
        self.root_group = root_group
        self.subcommand = subcommand
        self.subgroup = subgroup

    async def mock_context(self):
        message = libneko.aggregates.Proxy(_state=None)
        return libneko.Context(message=message, prefix=self.PREFIX)

    async def mock_invoke(self, command):
        setattr(self, "sema4", False)
        await command.callback(self, await self.mock_context())
        self.assertTrue(getattr(self, "sema4"))

    async def test_call_override_klazz_command(self):
        await self.do_setUp()
        await self.mock_invoke(self.root_command)
        self.assertIsInstance(self.root_command, self.CustomCommandKlazz)
        self.assertIsNone(self.root_command.parent)

    async def test_call_override_klazz_group(self):
        await self.do_setUp()
        await self.mock_invoke(self.root_group)
        self.assertIsInstance(self.root_group, self.CustomGroupKlazz)
        self.assertIsNone(self.root_group.parent)

    async def test_call_override_klazz_command_subcommand(self):
        await self.do_setUp()
        await self.mock_invoke(self.subcommand)
        self.assertIsInstance(self.subcommand, self.CustomCommandKlazz)
        self.assertIs(self.root_group, self.subcommand.parent)

    async def test_call_override_klazz_command_subgroup(self):
        await self.do_setUp()
        await self.mock_invoke(self.subgroup)
        self.assertIsInstance(self.subgroup, self.CustomGroupKlazz)
        self.assertIs(self.root_group, self.subgroup.parent)


class CommandMixinTest(asynctest.TestCase):
    def setUp(self):
        class Parent:
            name = "wassup"
            qualified_name = name

        class MixinMock(libneko.commands.CommandMixin):
            def __init__(self):
                kwargs = dict(
                    command_attributes={"foo": "bar", "baz": "bork"},
                    category="ayy",
                    examples="lmao",
                    name="foo",
                    aliases=["bar", "baz", "bork"],
                    parent=Parent(),
                )

                super().__init__(**kwargs)

                for k, v in kwargs.items():
                    setattr(self, k, v)

            async def callback(self, ctx, *args, **kwargs):
                return 123

        self.mixin_class = MixinMock
        self.mixin = self.mixin_class()
        self.parent = self.mixin.parent

    async def test_call(self):
        callback_result = await self.mixin.callback(object(), object(), foo=object())
        call_result = await self.mixin(object(), object(), foo=object())
        self.assertEqual(callback_result, call_result)

    def test_attributes(self):
        self.assertEqual({"foo": "bar", "baz": "bork"}, self.mixin.attributes)

    def test_all_names(self):
        all_names = "foo bar baz bork".split()
        for name in all_names:
            self.assertIn(name, [*self.mixin.all_names])

    def test_qualified_name(self):
        qn = "wassup foo"
        self.assertEqual(qn, self.mixin.qualified_name)

    def test_all_qualified_names(self):
        all_names = ["wassup foo", "wassup bar", "wassup baz", "wassup bork"]
        for name in all_names:
            self.assertIn(name, [*self.mixin.all_qualified_names])

    def test_qualified_aliases(self):
        all_names = ["wassup bar", "wassup baz", "wassup bork"]
        for name in all_names:
            self.assertIn(name, [*self.mixin.qualified_aliases])


class GroupTest(asynctest.TestCase):
    @libneko.commands.group()
    async def foo(self, ctx):
        pass

    @foo.group()
    async def bar(self, ctx):
        pass

    @bar.command()
    async def baz(self, ctx):
        pass

    @bar.command()
    async def bork(self, ctx):
        pass

    @foo.command()
    async def qux(self, ctx):
        pass

    @foo.group()
    async def quux(self, ctx):
        pass

    def test_walk_youngest_descendants(self):
        descendants = [*self.foo.walk_youngest_descendants()]
        self.assertIn(self.baz, descendants)
        self.assertIn(self.bork, descendants)
        self.assertIn(self.qux, descendants)
        self.assertEqual(3, len(descendants))
