from discord.ext import commands


class Example(commands.Cog):
	
	@commands.command(name='ping')
	async def ping_command(self, ctx):
		await ctx.send("Pong!!")

def setup(bot):
	bot.add_cog(Example())
