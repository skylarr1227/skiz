#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple option picker made using the pagination API. This is mostly as an example.
"""
__all__ = ("option_picker", "NoOptionPicked")

from typing import Any, Callable, Tuple, Union

from libneko.commands import Context
from libneko.embeds import Embed
from libneko.singleton import Singleton
from .factory import EmbedNavigatorFactory, embed_generator
from .navigator import CancelAction, FakeContext
from .reactionbuttons import next_page, previous_page


class NoOptionPicked(Singleton):
    """
    Singleton type used by :func:``option_picker``.

    This is returned if the user chose to cancel, and is falsified.
    """

    def __bool__(self):
        return False

    def __str__(self):
        return "No option was picked"


async def option_picker(
    *options,
    stringifier: Callable[[Any], str] = str,
    ctx: Union[FakeContext, Context, Tuple],
    prompt: str = "{author}: please pick an option",
    timeout: float = 300,
    max_lines: int = 6,
) -> Any:
    """
    Super-simple number-based option picker example for your convenience. This is displayed in an
    EmbedNavigator.

    The user is asked to either input ``cancel`` or a 1-based integer. This is then returned.

    Parameters: options: One or more objects to pick. If only one option is provided,
    then we just return that option immediately. stringifier: Defaults to :class:`str`. A
    function to produce a string from a given option for display. ctx: Either a fake context or a
    real context, or a tuple of context arguments. Tuples get converted to :class:`FakeContext`
    internally. prompt: A format string for a prompt. You can use ``{member}`` to interpolate the
    attribute ``member`` that belongs to the given ``context``. timeout: The timeout in seconds
    before raising an asyncio.TimeoutError. This must be a float or int. max_lines: The max
    number of lines to show per page.

    Returns: Either the selected option from the given list or an instance of the
    :class:`NoOptionPiked` singleton class if the user opted to cancel instead.
    """
    if isinstance(ctx, tuple):
        ctx = FakeContext(*ctx)

    if len(options) == 1:
        return options[0]
    elif len(options) == 0:
        raise ValueError("Cannot show option picker for zero options.")

    if not isinstance(timeout, (int, float)):
        raise TypeError("timeout must be a number")
    elif timeout <= 0:
        raise ValueError("timeout must be greater than zero.")

    @embed_generator(max_chars=2048, provides_numbering=False)
    def egen(_, page, __):
        members = {o: getattr(ctx, o) for o in dir(ctx)}
        return Embed(title=prompt.format(**members), description=page)

    buttons = [previous_page, next_page]

    pag = EmbedNavigatorFactory(max_lines=max_lines, factory=egen)
    pag.disable_truncation()

    pag.add_line("`cancel` - cancel this")

    for i, option in enumerate(options):
        pag.add_line(f"`{i + 1}` - {stringifier(option)}")

    def is_valid_option(input):
        input = input.lower()

        if input == "cancel":
            return True
        try:
            input = int(input)

            return 0 < input <= len(options)
        except ValueError:
            return False

    def predicate(response):
        return all(
            (
                response.author == ctx.message.author,
                response.channel == ctx.message.channel,
                is_valid_option(response.content),
            )
        )

    nav = pag.build(ctx, buttons=buttons)
    nav.start()

    async def get_option():
        while True:
            m = await ctx.bot.wait_for("message", check=predicate, timeout=timeout)

            try:
                await m.delete()
            except Exception:
                pass

            content = m.content

            if content.lower() == "cancel":
                return NoOptionPicked()
            else:
                option = int(content)

                if 0 < option <= len(options):
                    return options[option - 1]
                else:
                    await ctx.channel.send("Out of range...", delete_after=5)

    try:
        return await get_option()
    finally:
        nav.kill(CancelAction.REMOVE_ALL_MESSAGES)
