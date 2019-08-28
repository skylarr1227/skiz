from .core.dna import Bot
import discord
from discord.ext import commands
import aiohttp
import re
from datetime import timedelta
import traceback
import os
from random import choice, randint

#@bot.event
#async def on_ready():
#    print('Logged in as')
#    print(bot.user.name)
#    print(bot.user.id)
#    print('------')
#    print(discord.utils.oauth_url(bot.user.id))

Bot().run()
