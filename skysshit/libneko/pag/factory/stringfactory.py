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
A combination of a ``pag.Paginator`` and a ``pag.StringNavigator``.
"""

__all__ = ("StringNavigatorFactory",)

from typing import Union, Sequence

from discord.ext import commands

from ..navigator import FakeContext, StringNavigator
from ..paginator import Paginator
from ..reactionbuttons import Button, default_buttons


class StringNavigatorFactory(Paginator):
    """
    A paginator implementation that will build the desired StringNavigator.

    Example usage::

       snf = StringNavigatorFactory()

       for i in range(500):
           snf.add_line(f'{i}')

       snf.start(ctx)

    """

    def build(
        self,
        ctx: Union[commands.Context, FakeContext, tuple],
        buttons: Sequence[Button] = None,
        *,
        timeout: float = 300,
        initial_page: int = 0,
        **kwargs,
    ) -> StringNavigator:
        """
        Args:
            ctx: invocation context or fake context.
            buttons: buttons to show. If unspecified, this defaults to the defaultset of buttons.
            timeout: optional response timeout (defaults to 300 seconds)
            initial_page: the initial page index to start on (defaults to 0).

        Kwargs:
             attrs to assign the navigator.

        """
        if isinstance(ctx, tuple):
            ctx = FakeContext(*ctx)
        if buttons is None:
            buttons = default_buttons()

        n = StringNavigator(
            ctx, self.pages, buttons=buttons, timeout=timeout, initial_page=initial_page
        )
        for k, v in kwargs:
            setattr(n, k, v)
        return n

    def start(
        self,
        ctx: Union[commands.Context, FakeContext],
        buttons: Sequence[Button] = None,
        *,
        timeout: float = 300,
        initial_page: int = 0,
        **kwargs,
    ):
        """
        Same as performing ``.build(...).start()``
        """
        return self.build(
            ctx, buttons, timeout=timeout, initial_page=initial_page, **kwargs
        ).start()
