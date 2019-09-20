from discord.ext import commands

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
        if (message.mentions.__len__()>0):
        for user in message.mentions:
        print(user.avatar_url)

def setup(bot):
    bot.add_cog(Events(bot))
