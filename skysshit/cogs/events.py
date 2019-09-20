import discord
from discord.ext import commands

client = discord.Client()


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Ready!')
        print('Logged in as ---->', self.bot.user)
        print('ID:', self.bot.user.id)

    @commands.Cog.listener()
    async def on_message(self, message):
    if message.author == client.user:
        return

    if message.content.startswith('>avatar'):
        if len(message.mentions) > 0:
            images = ''
            for user in message.mentions:
                images += str(user.avatar_url) + str('\n')
            await message.channel.send(images)
        else:
            await message.channel.send(message.author.avatar_url)




def setup(bot):
    bot.add_cog(Events(bot))
