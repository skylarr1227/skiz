import discord
from discord.ext import commands
import aiohttp
import re
from datetime import timedelta
import traceback
import os
from random import choice, randint 

owner = [""] 

class Example(commands.Cog):

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    print(discord.utils.oauth_url(bot.user.id))

@bot.event
async def on_command_error(error, ctx):
    channel = ctx.message.channel 
    if isinstance(error, commands.MissingRequiredArgument):
        await send_cmd_help(ctx) 
    elif isinstance(error, commands.BadArgument):
        await send_cmd_help(ctx)
    elif isinstance(error, commands.CommandInvokeError):
        print("Exception in command '{}', {}".format(ctx.command.qualified_name, error.original))
        traceback.print_tb(error.original.__traceback__)


@bot.event async 
def send_cmd_help(ctx):
    if ctx.invoked_subcommand:
        pages = bot.formatter.format_help_for(ctx, ctx.invoked_subcommand)
        for page in pages:
            em = discord.Embed(description=page.strip("```").replace('<', '[').replace('>', ']'),
                                color=discord.Color.blue()) 
            await bot.send_message(ctx.message.channel, embed=em)
    else: 
        pages = bot.formatter.format_help_for(ctx, ctx.command)
        for page in pages:
            em = discord.Embed(description=page.strip("```").replace('<', '[').replace('>', ']'), 
                                color=discord.Color.blue())
            await bot.send_message(ctx.message.channel, embed=em)


	
@commands.command(name='ping')
async def ping_command(self, ctx):
    await ctx.send("Pong!!")




def setup(bot):
    bot.add_cog(Example())
