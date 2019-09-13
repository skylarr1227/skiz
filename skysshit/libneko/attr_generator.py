#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# MIT License
#
# Copyright (c) 2018-2019 Flitt3r (a.k.a Koyagami)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in a$
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
Utilities for the attribute generation system for commands. This allows super-fast
and simple association of basic custom attributes with your commands. These can
be inpsected to see if they are present, or what value they contain, very easily.

Example::

        make_cool_command = attr_generator('is_cool', True)

        ...

        @make_cool_command
        @commands.command()
        async def cool_command(ctx):
            await ctx.send('This is cool.')


        @commands.command()
        async def uncool_command(ctx):
            await ctx.send('So uncool.')

        ...

        assert cool_command.attributes['is_cool']
        assert not uncool_command.attributes['is_cool']

Author:
    Espy/Neko404NotFound

"""

__all__ = ("attr_generator",)

from collections import defaultdict


def attr_generator(key, value):
    """
    Generates a decorator for a command to apply some simple
    key-value attribute to it. If no attribute is associated, the
    ``Command`` implementation assumes the value to be ``None``.

    Example usage::

        make_cool_command = attr_generator('is_cool', True)

        ...

        @make_cool_command
        @commands.command()
        async def cool_command(ctx):
            await ctx.send('This is cool.')


        @commands.command()
        async def uncool_command(ctx):
            await ctx.send('So uncool.')

        ...

        assert cool_command.attributes['is_cool']
        assert not uncool_command.attributes['is_cool']

    """

    def _get_append_attribute(cmd):
        from libneko.commands import Command

        if not isinstance(cmd, Command):
            raise TypeError(
                "Applied attribute to non libneko Command. "
                "I cannot guarantee this implementation will "
                "handle this correctly."
            )

        if "__command_attributes__" not in dir(cmd):
            setattr(cmd, "__command_attributes__", defaultdict(None))
        cmd.__command_attributes__[key] = value
        cmd.__dict__[key] = value
        return cmd

    return _get_append_attribute
