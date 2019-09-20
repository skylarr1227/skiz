from discord.ext import commands
from libneko import pag

with open('skysshit/cogs/dummy-text.txt') as fp:
    dummy_text = fp.read()
with open('skysshit/cogs/plancan.txt') as file1:
    plancan = file1.read()

plancan_gif = 'http://157.245.8.88:8000/55ef51a74f091dad52a9bca3bccfb6cb.png'

class Skybot(commands.Cog):
	
        @commands.command()
        async def skybot(self, ctx):
            """A quick and organized help menu for Skybot"""
            nav = pag.EmbedNavigatorFactory(max_lines=10)
            nav += dummy_text
            nav.start(ctx)

        @commands.command()
        async def plancan(self, ctx):
            """Rules and information regarding PlanCan"""
            nav = pag.EmbedNavigatorFactory(max_lines=10)
            nav += plancan
            nav.start(ctx)

        @pag.embed_generator(max_chars=2048)
        def plancan_embed(paginator, page, page_index):
            embed = discord.Embed(colour=0xbfff00, description=page)
            embed.set_image(url=plancan_gif)
            return embed


def setup(bot):
        bot.add_cog(Skybot())
