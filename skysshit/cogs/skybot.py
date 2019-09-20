import discord
from discord.ext import commands
from libneko import pag

with open('skysshit/cogs/dummy-text.txt') as fp:
    dummy_text = fp.read()
with open('skysshit/cogs/plancan.txt') as file1:
    plancan = file1.read()

plancan_gif = 'http://157.245.8.88:8000/55ef51a74f091dad52a9bca3bccfb6cb.png'

class Skybot(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
        #@pag.embed_generator(max_chars=2048)
        #def plancan_embed(paginator, page, page_index):
        #    embed = discord.Embed(colour=0xbfff00, description=page)
        #    embed.set_image(url=plancan_gif)
        #    return embed

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

        @commands.command(name='infos' , aliases=["i"])
        async def infos(self, ctx,):   
            infostuff=ctx.message
            infostuff=str(infostuff.content)
            infostuff=infostuff.replace("-info","")
            infostuff=infostuff.replace(" ",",")
            info=info.split(',')
            info.append('-')
            if infostuff[1]=="-":
                stuff=ctx.author.avatar_url
            elif infostuff[1].isdigit()==True: "or discord.Member"
            stuff=infostuff[1].avatar.url
            """embed stuff where url=stuff"""
            await ctx.send(embed=embed)


def setup(bot):
        bot.add_cog(Skybot(bot))
