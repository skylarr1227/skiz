import os
import discord
from discord.ext import commands
import aiohttp
from datetime import timedelta
from random import choice, randint
import libneko
from discord import Embed
from discord.ext.commands import is_owner

class Bot(commands.Bot):
	def __init__(self, *args, **kwargs):
		super().__init__(command_prefix="_", *args, **kwargs)
		self.token = os.environ["TOKEN"]
		self.skybot_cogs = [ext for ext in os.listdir("skysshit/cogs") if ext.endswith(".py")]
	
	async def load_extensions(self):
		for ext in self.skybot_cogs:
			print("Loading %s" % ext)
			self.load_extension(f"skysshit.cogs.{ext[:-3]}")
			print("Loaded %s" % exit)
class Modules:
	def __init__(self, bot: commands.Bot):
        	self.bot = bot
        	print('Addon "{}" loaded'.format(self.__class__.__name__))

	@commands.group(hidden=True)
	@is_owner()
	async def module(self, ctx):
        	if ctx.invoked_subcommand is None:
        	await ctx.send(embed=Embed(title="Module Commands", color=0x9b006f,
                	description=f"There are actually 3 Commands to use.\n "
                        	f"All Commands in this Group are Bot-Owner only!\n\n"
                        	f"{ctx.prefix}module load <ModuleName> || "
                        	f"Loads a Module\n"
                        	f"{ctx.prefix}module unload <ModuleName> || "
                        	f"Unloads a Module\n"
                        	f"{ctx.prefix}module load <ModuleName> || "
                        	f"Reloads a Module"))

    	@module.command()
    	async def load(self, ctx, *, cog: str):
        """Load a Module."""
        try:
        	self.bot.load_extension(f'modules.{cog}')
        except Exception as e:
        	await ctx.send(embed=Embed(description='**`ERROR:`** {} - {}'.format(type(e).__name__, e)))
        else:
        	await ctx.send(embed=Embed(title=f'\u2705 **`SUCCESS`**: Addon "{str.title(cog)}" loaded',
                                       colour=0x187E03))

    	@module.command()
    	async def unload(self, ctx, *, cog: str):
        """Unload a Module."""
	try:
        	self.bot.unload_extension(f'modules.{cog}')
	except Exception as e:
        	await ctx.send(embed=Embed(description='**`ERROR:`** {} - {}'.format(type(e).__name__, e)))
	else:
        	await ctx.send(embed=Embed(title=f'\u2705 **`SUCCESS`**: Addon "{str.title(cog)}" unloaded',
                                       colour=0x187E03))

	@module.command()
	async def reload(self, ctx, *, cog: str):
	"""Reload a Module."""
	try:
        	self.bot.unload_extension(f'modules.{cog}')
        	self.bot.load_extension(f'modules.{cog}')
	except Exception as e:
        	await ctx.send(embed=Embed(description='**`ERROR:`** {} - {}'.format(type(e).__name__, e)))
	else:
        	await ctx.send(embed=Embed(title=f'\u2705 **`SUCCESS`**: Addon "{str.title(cog)}" '
                                         f'reloaded', colour=0x187E03))
	
		
	async def on_ready(self):
	        print("Ready!")
	        await self.load_extensions()
	
        def run(self):
	        super().run(self.token)
