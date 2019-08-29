from discord.ext import commands

class ExampleCog(commands.Cog):
	
	@commands.command()
	async def ping(self, ctx):
		await ctx.send("Pong!")
		

def setup(bot):
	bot.add_cog(ExampleCog())
