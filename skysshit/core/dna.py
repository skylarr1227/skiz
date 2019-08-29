import os
import discord
from discord.ext import commands
import aiohttp
from datetime import timedelta
from random import choice, randint



class Bot(commands.Bot):

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    print(discord.utils.oauth_url(bot.user.id))

	def __init__(self, *args, **kwargs):
		super().__init__(command_prefix="_", *args, **kwargs)
		self.token = os.environ["TOKEN"]
		self.skybot_cogs = os.listdir("skysshit/cogs")
	
	async def load_extensions(self):
		for ext in self.extensions:
			self.load_extension(ext)
		
	async def on_ready(self):
		print("Ready!")
		await self.load_extensions()
	
	def run(self):
		super().run(self.token)
