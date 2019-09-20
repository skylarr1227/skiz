import discord
from discord.ext import commands
from libneko import pag

with open('skysshit/cogs/dummy-text.txt') as fp:
    dummy_text = fp.read()
with open('skysshit/cogs/plancan.txt') as file1:
    plancan = file1.read()

plancan_gif = 'http://157.245.8.88:8000/55ef51a74f091dad52a9bca3bccfb6cb.png'

class Skybot(commands.Cog):

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

        @commands.command(aliases=["playerstats", "player", "userinfo", "userstats", "user"])
        async def playerinfo(self, ctx, *, user: discord.Member = None):
            """
            Gives you player info on a user. If a user isn't passed then the shown info is yours.
            """
            if not user:
                user = ctx.author

            roles = [role.name.replace("@", "@\u200b") for role in user.roles]
            share = sum(1 for m in self.bot.get_all_members() if m.id == user.id)
            voice_channel = user.voice
            if voice_channel is not None:
                voice_channel = voice_channel.channel.name
            else:
                voice_channel = "Not in a voice channel."

            msg = [
                ("Name", user.name), ("Discrim", user.discriminator),
                ("ID", user.id),
                ("Display Name", user.display_name),
                ("Joined at", user.joined_at),
                ("Created at", user.created_at),
                ("Server Roles", ", ".join(roles)),
                ("Color", user.color),
                ("Status", user.status),
                ("Game", user.game),
                ("Voice Channel", voice_channel),
                ("Servers Shared", share),
                ("Avatar URL", user.avatar_url)
            ]

            await ctx.send()


def setup(bot):
        bot.add_cog(Skybot())
