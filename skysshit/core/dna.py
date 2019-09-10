import os
import discord
from discord.ext import commands
import aiohttp
from datetime import timedelta
from random import choice, randint
import libneko
from discord import Embed
from discord.ext.commands import is_owner

import time
from collections import Counter, deque
from pathlib import Path

from pyppeteer import launch, errors

from bot.utils.logging import setup_logger
from bot.utils.over import send


discord.abc.Messageable.send = send



class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(command_prefix="_", *args, **kwargs)
        self.token = os.environ["TOKEN"]
        self.skybot_cogs = [ext for ext in os.listdir("skysshit/cogs") if ext.endswith(".py")]
	       # self.session = aiohttp.ClientSession(loop=self.loop, headers={"User-Agent"=self.http.user_agent)
                #self.browser_page = None
             #   self.browser = self.loop.create_task(self.create_browser())
               # self.priv = self.config['extras'].get('privatebin', 'https://privatebin.net')
               # self.polr = self.config['extras'].get('polr', None)
#
        self.commands_used = Counter()
        self.commands_used_in = Counter()
        self.errors = deque(maxlen=10)
        self.revisions = None

        discord_logger = setup_logger("discord")
        self.logger = setup_logger("Bot")
        self.command_logger = setup_logger("Commands")
        self.loggers = [discord_logger, self.logger, self.command_logger]

        _modules = [mod.stem for mod in Path("skysshit/cogs").glob("*.py")]
        self.load_extension(f"skysshit.cogs.core")
        self.load_extension(f"skysshit.cogs.owner")
        if 'bare' in kwargs.pop('argv'):  # load the bot bare-bones to diagnose issues
            return
        for module in _modules:
            try:
                if module in ['core', 'errors']:
                    pass
                self.load_extension(f"skysshit.cogs.{module}")
            except discord.DiscordException as exc:
                self.logger.error(f"{type(exc).__name__} occurred when loading {module}: {exc}")

        # make sure to only print ready text once
        self._loaded = False
        async def on_ready(self):
            """Function called when bot is ready or resumed"""
            if self._loaded is False:
                end_time = time.time() - self.start_time
                self.app_info = await self.application_info()
                self.logger.info(f"Loaded Bot:")
                self.logger.info(f"Logged in as {self.user}")
                self.logger.info(f"ID is {self.user.id}")
                self.logger.info(f"Owned by {self.app_info.owner}")
                self.description = f"Hello, this is the help menu for {self.user.name}!"
                self.logger.info(f"Bot started in {end_time} seconds")
                self._loaded = True
        print("Ready!")
        #await self.load_extensions()

        async def create_browser(self):
            """Task to create browser for scraping purposes."""
            await self.wait_until_ready()
            self.browser = await launch(args=["--no-sandbox"], headless=True)
            self.browser_page = await self.browser.newPage()
            
        async def load_extensions(self):
            for ext in self.skybot_cogs:
                print("Loading %s" % ext)
                self.load_extension(f"skysshit.cogs.{ext[:-3]}")
                print("Loaded %s" % exit)
                
                

        async def on_ready(self):
            print("Ready!")
            await self.load_extensions()
	def run(self):
            super().run(self.token)
