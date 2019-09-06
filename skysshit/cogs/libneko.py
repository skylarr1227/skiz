#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import logging

import async_timeout
import discord


NEXT = '\N{BLACK RIGHT-POINTING TRIANGLE}'
PREVIOUS = '\N{BLACK LEFT-POINTING TRIANGLE}'
CLOSE = '\N{REGIONAL INDICATOR SYMBOL LETTER X}'


class Navigator:
    LOGGER = logging.getLogger(__name__)

    def __init__(self, title, bot, channel, owner, pages, timeout=300, color=0xb3f9ff):
        if len(pages) == 0:
            raise RuntimeError("Can't send a navigator with no pages.")

        self.title = title
        self.bot = bot
        self.channel = channel
        self.owner = owner
        self.color = color
        self.timeout = timeout
        self.pages = pages
        self._page_index = 0
        self._event = None
        self._message = None
        self._page_turn_channel = asyncio.Event()
        self._page_turn_task = None

    @property
    def page_index(self):
        return self._page_index

    @page_index.setter
    def page_index(self, index):
        self._page_index = index % len(self.pages)
        self._page_turn_channel.set()

    @property
    def page(self):
        return self.pages[self.page_index]

    @property
    def rendered_page(self):
        e = discord.Embed(title=self.title, color=self.color, description=self.page)
        e.set_author(name="Sinon", icon_url=self.bot.user.avatar_url)
        e.set_footer(text=f"{self.page_index + 1} of {len(self.pages)}")
        return e
    def go_forward(self):
        self.page_index += 1
        return self.rendered_page

    def go_back(self):
        self.page_index -= 1
        return self.rendered_page

    def run(self):
        return asyncio.create_task(self._run())

    async def _run(self):
        try:
            self._message = await self.channel.send(embed=self.rendered_page)

            @self.bot.listen("on_reaction_add")
            @self.bot.listen("on_reaction_remove")
            @self.bot.listen("on_message_delete")
            async def on_event(*args):
                if len(args) == 1:
                    if args[0].id == self._message.id:
                        self._page_turn_task.cancel()
                else:
                    r, u = args
                    if r.message.id == self._message.id and u == self.owner:
                        await self._dispatch(r)

            try:
                self.bot.add_listener(on_event)
                self._page_turn_task = asyncio.create_task(self.page_timeout_listener())
                await asyncio.gather(self._page_turn_task, self._add_initial_reactions())
                self._message.clear_reactions()
            finally:
                self.bot.remove_listener(on_event)

        except discord.HTTPException as ex:
            self.LOGGER.exception("Ignoring exception", exc_info=ex)

    async def _dispatch(self, reaction):
        emoji = reaction.emoji

        if emoji == NEXT:
            await self._message.edit(embed=self.go_forward())
        elif emoji == PREVIOUS:
            await self._message.edit(embed=self.go_back())
        elif emoji == CLOSE:
            self._page_turn_task.cancel()
            await self._message.delete()
    async def _add_initial_reactions(self):
        await self._message.add_reaction(PREVIOUS)
        await self._message.add_reaction(CLOSE)
        await self._message.add_reaction(NEXT)

    async def page_timeout_listener(self):
        while True:
            try:
                async with async_timeout.timeout(self.timeout):
                    await self._page_turn_channel.wait()
                    self._page_turn_channel.clear()
            except asyncio.TimeoutError:
                break

    @classmethod
    def from_context(cls, ctx, pages, **kwargs):
        return cls(kwargs.pop("title", ""), ctx.bot, ctx.channel, ctx.author, pages, **kwargs)
