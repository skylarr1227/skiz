# Bruh
import sys
import asyncio
import .permissions
import patterns
import utils.util as util
import discord
from configparser import ConfigParser
from discord.ext import commands
from pipes.processor import PipelineProcessor


bot = commands.Bot(command_prefix=command_prefix)
command_prefix = config['BOT']['prefix'] 
pipe_prefix = config['BOT']['pipe_prefix']
patterns = patterns.Patterns(bot)
pipeProcessor = PipelineProcessor(bot, pipe_prefix)


@bot.event
async def on_message(message):    
    if message.author.id == bot.user.id:
        return
    
    if permissions.is_muted(message.author.id):
        return
    
    if message.author.bot:
        return

    # Try for text pipes, if it's a pipe, don't look for anything else.
    if await pipeProcessor.process_script(message):
        return

    # Try for patterns if it doesn't look like a command
    if(message.content[:len(command_prefix)] != command_prefix):
        await pipeProcessor.on_message(message)
        await patterns.process_patterns(message)
    # Try for commands
    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    print('')
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.author.send('Wow, dont say another word to me that is simply not okay in private.')
    elif isinstance(error, commands.DisabledCommand):
        await ctx.author.send('Sorry motherfucker. This command is fucking disabled, jokes on you.')
    elif isinstance(error, commands.CommandInvokeError):
        print('In {0.command.qualified_name}:'.format(ctx), file=sys.stderr)
        # traceback.print_tb(error.original.__traceback__)
        print('{0.__class__.__name__}: {0}'.format(error.original), file=sys.stderr)
    else:
        print('Command Error:', error)


    if __name__ == '__main__':    
        bot.load_extension('pipes.pipecommands')
        bot.load_extension('pipes.macrocommands')
        bot.load_extension('resource.youtubecaps.commands')
        bot.load_extension('resource.upload.commands')

Bot().run()
