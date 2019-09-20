from discord.ext import commands
from libneko import pag

with open('dummy-text.txt') as fp:
    dummy_text = fp.read()


class Skybot(commands.Cog):
	
        @commands.command()
        async def skybot(self, ctx):
        """A quick and organized help menu for Skybot"""
            nav = pag.EmbedNavigatorFactory(max_lines=10)
            nav += dummy_text
            nav.start(ctx)

def setup(bot):
        bot.add_cog(Skybot())
