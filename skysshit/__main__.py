#from .core.dna import Bot
import asyncio
import logging
import os




TOKEN = os.environ['TOKEN']

#bot = self.bot()
#Bot = self.bot() 

#@bot.event
#async def on_ready(self):
#    print('Logged in as')
#    print(bot.user.name)
#    print(bot.user.id)
#    print('------')
#    print(discord.utils.oauth_url(bot.user.id))

#@bot.command () 
#sync def load ( extension_name : str ): 
#    """ Loads an extension. """ 
#    try : 
#        bot.load_extension(extension_name) 
#    except ( AttributeError , ImportError ) as e: 
#        await bot.say( " ```py \n {} : {} \n ``` " .format( type (e). __name__ , str (e))) 
#    return 
#    await bot.say( " {} loaded. " .format(extension_name)) 
 


Bot().run()
