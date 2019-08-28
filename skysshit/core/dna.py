import os
import discord as discord
from discord.ext import commands
import aiohttp
import re
from datetime import timedelta
import traceback
import os
from random import choice, randint



class Bot(commands.Bot):

#@bot.event
#async def on_ready():
#    print('Logged in as')
 #   print(bot.user.name)
#    print(bot.user.id)
#    print('------')
#    print(discord.utils.oauth_url(bot.user.id))

	def __init__(self, *args, **kwargs):
		super().__init__(command_prefix="_", *args, **kwargs)
		self.token = os.environ["TOKEN"]
	
	def run(self):
		client = discord.Client()
		client.run(self.token)
