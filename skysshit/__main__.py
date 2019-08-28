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

@bot.command () 
async def load ( extension_name : str ): 
    """ Loads an extension. """ 
    try : 
        bot.load_extension(extension_name) 
    except ( AttributeError , ImportError ) as e: 
        await bot.say( " ```py \n {} : {} \n ``` " .format( type (e). __name__ , str (e))) 
    return 
    await bot.say( " {} loaded. " .format(extension_name)) 
 


Bot().run()
