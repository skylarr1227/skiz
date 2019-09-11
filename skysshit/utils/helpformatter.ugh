import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help', aliases=['h'])
    async def _help(self, ctx, *, command: str=None):
        """Get help on a specified cog or command.
        Don't put any arguments to get a list of available commands."""
        pref = '```\n'
        postf = f'Get info on a command group, category or just a command with @{self.bot.user.name}#{self.bot.user.discriminator} help <Category>/<Command>/<Command group> or *help <Category>/<Command>/<Command group>'
        result = ''
        postfix = '\n```'
        paginator = commands.Paginator()
        if not command:
            li = [cog for cog in self.bot.cogs]
            for smth in li:
                if smth != 'Help':
                    s = list(self.bot.cogs[smth].get_commands())
                    if s:
                        paginator.add_line(f"{s[0].cog_name}:")
                        for c in s:
                            if not c.hidden:
                                paginator.add_line(f'    {c.name} - {c.short_doc}')
            paginator.add_line(postf)
            for page in paginator.pages:
                await ctx.send(page)
        else:
            if command not in self.bot.all_commands:
                if command not in self.bot.cogs:
                    cmd = self.bot.get_command(command.replace('*', '').replace(self.bot.user.mention, ''))
                    if cmd:
                        paginator.add_line(f"{ctx.prefix.replace(self.bot.user.mention, f'@{self.bot.user.name}#{self.bot.user.discriminator} ')}{cmd.signature}\n\n    {cmd.help}")
                        for page in paginator.pages:
                            await ctx.send(page)
                    else:
                        result = 'That command/category/command group does not exist!'
                        await ctx.send(result)
                else:
                    the_cog = list(command.get_commands())
                    paginator.add_line(f"{the_cog[0].cog_name}:") 
                    for cmd in the_cog:
                        if not cmd.hidden:
                            paginator.add_line(f'    {cmd.name} - {cmd.help}')
                    paginator.add_line(postf)
                    for page in paginator.pages:
                        await ctx.send(page)
            else:
                cmd = self.bot.get_command(command.replace('*', '').replace(self.bot.user.mention, ''))
                result += f"{ctx.prefix.replace(self.bot.user.mention, f'@{self.bot.user.name}#{self.bot.user.discriminator} ')}{cmd.signature}\n\nCog: {cmd.cog_name}\n\n    {cmd.help}"
                await ctx.send(f"{pref}{result}{postfix}")

def setup(bot):
    bot.add_cog(Help(bot))



