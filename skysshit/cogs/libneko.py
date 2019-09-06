import discord
import libneko
from discord.ext import commands
from libneko import pag

# Read the dummy text in.

class Libneko(commands.Cog):
    #def __init__(self)
    
    @commands.command()
    async def test(ctx):
        try:
            with open('dummy-text.txt') as fp:
                dummy_text = fp.read()
        except:
            await ctx.send("Could not read")
        """We will be coding in here in the next part."""
        nav = pag.StringNavigatorFactory(max_lines=10)

        # Insert the dummy text into our factory.
        nav += dummy_text

        nav.start(ctx)

def setup(bot):
    bot.add_cog(Libneko(bot))
