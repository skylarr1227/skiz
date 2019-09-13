#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Literally just so I can test stuff.
"""
import asyncio
import logging
import os
import time
import traceback

import aiohttp

from libneko import commands, pag, clients, converters
from libneko.extras import superuser


logging.basicConfig(level="DEBUG")


bot = clients.Bot(command_prefix="lnt!")
bot.loop.set_debug(True)


bot.load_extension("libneko.extras.superuser")


class OverriddenSuperUserCog(superuser.SuperuserCog):
    pass


# bot.add_cog(OverriddenSuperUserCog())


@bot.command()
async def paginator(ctx, *, url):
    """Gets the content of a specific webpage endpoint and paginates it."""
    p = pag.StringNavigatorFactory(max_lines=20, prefix="```http", suffix="```")
    async with aiohttp.request("get", url) as resp:
        content = await resp.text()
        p.add_line(f"{resp.status} {resp.method} {resp.url}")
        for k, v in resp.headers.items():
            p.add_line(f'{k}:{v}')
        p.add(content)

    p.start(ctx)


@commands.is_owner()
@bot.command()
async def unhandle(ctx):
    """Raise an unhandled error."""
    raise RuntimeError(ctx)


@bot.event
async def on_connect():
    bot.owner_id = (await bot.application_info()).owner.id


@bot.event
async def on_logout():
    print("ded")


@bot.event
async def on_command_error(ctx, error):
    try:
        traceback.print_exception(type(error), error, error.__traceback__)

        p = pag.Paginator(prefix="```py", suffix="```")
        ex = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        p.add_lines(*ex.splitlines(keepends=False))

        for page in p.pages:
            await ctx.send(page)
    except Exception:
        traceback.print_exc()


@bot.no_block
def foo(t):
    time.sleep(t)


@bot.command()
async def test_sleep(ctx):
    async with ctx.typing():
        await foo(20)
    await ctx.send("Done")


@bot.command()
async def opt(ctx):
    options = ['foo', 'bar', 'baz', 'bork', 'qux', 'quux', 'quuux']

    try:
        o = await pag.option_picker(*options, ctx=ctx, timeout=15)
        if o is pag.NoOptionPicked:
            await ctx.send('you cancelled it.')
        else:
            await ctx.send(o)
    except asyncio.TimeoutError:
        await ctx.send('You timed out...')


@bot.command()
async def insensuser(ctx, *, user: converters.InsensitiveUserConverter):
    await ctx.send(user.mention)


@bot.command()
async def insensmember(ctx, *, user: converters.InsensitiveMemberConverter):
    await ctx.send(user.mention)


bot.load_extension('libneko.extras.help')
bot.run(os.getenv("TOKEN"))
