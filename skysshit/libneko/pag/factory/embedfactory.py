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
Many people requested that there be a way to produce embeds using a factory, similar to
the ``StringNavigatorFactory``. Unfortunately, this is kind of complex to implement, as
embeds have multiple attributes and the settings each user may want can vary. Thus, to
simplify this, we have an ``AbstractEmbedGenerator`` that contracts a specific template
for creating an embed.

It specifically contains a property to get the max size of a  single page (as it depends
on the attribute being filled in the embed as to what the maximum constraint for size is.
A ``build_page`` method will take the paginator object, page content and page index, and is
expected to return a formatted embed.

A default implementation is provided for sanity, but it is up to the user to subclass this
generator if they want something more specific.

Since classes are kind of bulky-looking, a decorator factory is also provided to produce
these generators a bit easier. See each class and method for specific usage info.
"""
__all__ = (
    "EmbedNavigatorFactory",
    "AbstractEmbedGenerator",
    "DefaultEmbedGenerator",
    "embed_generator",
)

from typing import Union, Sequence, List

import discord
from discord.ext import commands

from libneko import embeds
from libneko.pag.factory.basefactory import BaseFactory
from ..navigator import FakeContext, EmbedNavigator
from ..paginator import Paginator
from ..reactionbuttons import Button, default_buttons


class AbstractEmbedGenerator:
    """
    Factory prototype that consumes pages and formats an embed with that data, before returning it.
    """

    @property
    def max_chars(self) -> int:
        """Returns the max characters allowed per page."""
        raise NotImplementedError("Abstract property max_chars must be overridden.")

    @property
    def provides_numbering(self) -> bool:
        """
        Returns whether or not we provide page numbering in the embed. If this is true, the
        navigator suppresses any page numbers in the content of the message itself.
        """
        raise NotImplementedError("Abstract property provides_page_numbering must be overridden.")

    def build_page(self, paginator: Paginator, page: str, page_index: int) -> discord.Embed:
        """
        Builds a given string page into an embed and returns the embed.

        Args:
            paginator:
                The paginator object we are working with.
            page:
                The string content to put into an embed.
            page_index:
                The 0-based page index.

        Returns:
            An embed containing the ``page`` string somewhere.
        """
        raise NotImplementedError("Abstract method build_page must be overridden.")


# noinspection PyUnresolvedReferences
def embed_generator(*, max_chars: int, provides_numbering=False):
    """
    Produces a subclass of ``AbstractEmbedGenerator`` with the decorated function
    body as the ``build_page`` method implementation.

    Keyword Args:
        max_chars:
            The max number of characters to allow per page.
        provides_numbering:
            True if the embed navigator factory using this embed generator should
            suppress adding page numbers. This usually implies that we are dealing
            with adding the page numbers into the embed ourselves. Defaults to
            False.

    Decorated function:
        A function that returns an embed somehow. This is up to you to implement, but the
        function must take three parameters: ``paginator`` (the paginator object calling this),
        ``page`` (the string page to make an embed from) and ``page_index`` (a 0-based int representing
        the page index number (e.g. page 5 will be 4)).

    Note:
        You can get the total number of pages by calling ``len(paginator.pages)`` as usual. This is
        pre-emptively generated: you will not incur a massive performance hit for using this.

    Returns:
         A class for an embed generator.

    Example usage::

        >>> @embed_generator(max_chars=2048)
        ... def mk_red_page(paginator, page, index):
        ...     return discord.Embed(colour=0xFF0000, description=page)

        >>> pag = EmbedNavigatorFactory(factory=mk_red_page)

    """
    if max_chars <= 0:
        raise ValueError("Invalid character limit.")

    # Prevents naming conflicts below.
    max_chars_ = max_chars
    provides_numbering_ = provides_numbering

    def decorator(factory_func):
        class __MetaFactory(AbstractEmbedGenerator):
            max_chars = max_chars_
            provides_numbering = provides_numbering_
            build_page = staticmethod(factory_func)

        __MetaFactory.__doc__ = getattr(factory_func, "__doc__", None)
        __MetaFactory.__name__ = getattr(factory_func, "__name__", None)
        __MetaFactory.__qualname__ = getattr(factory_func, "__qualname__", None)

        return __MetaFactory

    return decorator


class DefaultEmbedGenerator(AbstractEmbedGenerator):
    """
    A default embed generator that is not very customisable.

    This uses libneko.Embed default settings, but adds a page number to the embed in the
    footer. This means
    """

    @property
    def max_chars(self) -> int:
        return 2048

    @property
    def provides_numbering(self):
        return True

    def build_page(self, paginator: Paginator, page: str, page_index: int) -> discord.Embed:
        embed = embeds.Embed()

        embed.description = page
        embed.set_footer(text=f"p.{page_index+1} of {len(paginator.pages)}")

        return embed


class EmbedNavigatorFactory(BaseFactory, Paginator):
    """
    A type of paginator for producing embed pages. This is highly customisable
    by the ``factory`` parameter which takes an object that defines the way to
    produce an embed from text. You can override this by using the ``embed_generator``
    decorator, or by subclassing ``AbstractEmbedGenerator`` and providing an
    instance to this object.

    Note that, if supplied, ``max_chars`` will override the setting for max length
    of a page that is set in the ``factory`` parameter or default value.
    """

    def __init__(
        self,
        factory: AbstractEmbedGenerator = None,
        max_chars: int = None,
        max_lines: int = None,
        prefix: str = "",
        suffix: str = "",
        line_break: str = "\n",
        enable_truncation: bool = True,
        force_truncation: bool = True,
    ) -> None:

        if factory is None:
            factory = DefaultEmbedGenerator

        # If a class, we need the instance.
        if isinstance(factory, type):
            factory = factory()

        self.factory = factory

        self._suppress_page_numbers = self.factory.provides_numbering

        super().__init__(
            max_chars=max_chars or factory.max_chars,
            max_lines=max_lines,
            prefix=prefix,
            suffix=suffix,
            line_break=line_break,
            enable_truncation=enable_truncation,
            force_truncation=force_truncation,
        )

    def _transform_pages(self) -> List[discord.Embed]:
        """Converts string pages to embed pages."""
        # We need to pre-emptily get this.

        embed_pages = []

        for i, page in enumerate(self.pages):
            try:
                embed_pages.append(self.factory.build_page(self, page, i))
            except Exception as ex:
                raise ValueError(f"{type(ex).__name__} raised while producing page {i}.") from ex

        return embed_pages

    def build(
        self,
        ctx: Union[commands.Context, FakeContext, tuple],
        buttons: Sequence[Button] = None,
        *,
        timeout: float = 300,
        initial_page: int = 0,
        **kwargs,
    ) -> EmbedNavigator:
        """
        Args:
            ctx: invocation context or fake context.
            buttons: buttons to show. If unspecified, this defaults to the default set of buttons.
            timeout: optional response timeout (defaults to 300 seconds)
            initial_page: the initial page index to start on (defaults to 0).

        Kwargs:
             attrs to assign the navigator.

        """
        if isinstance(ctx, tuple):
            ctx = FakeContext(*ctx)
        if buttons is None:
            buttons = default_buttons()

        n = EmbedNavigator(
            ctx,
            self._transform_pages(),
            buttons=buttons,
            timeout=timeout,
            initial_page=initial_page,
        )

        if self._suppress_page_numbers:
            n.format_page_number = lambda: ""

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
