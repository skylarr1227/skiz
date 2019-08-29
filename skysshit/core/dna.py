import os
import discord
from discord.ext import commands
import aiohttp
from datetime import timedelta
from random import choice, randint



class Bot(commands.Bot):

	def __init__(self, *args, **kwargs):
		super().__init__(command_prefix="_", *args, **kwargs)
		self.token = os.environ["TOKEN"]
		self.skybot_cogs = os.listdir("skysshit/cogs")
	
	async def load_extensions(self):
		for ext in self.extensions:
			print("Loading %s" % ext)
			self.load_extension(ext)
			print("Loaded %s" % exit)
		
	async def on_ready(self):
		print("Ready!")
		await self.load_extensions()
	
	def run(self):
		super().run(self.token)
