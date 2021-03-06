from discord.ext import commands
from discord.ext.commands import errors

def bot_needs(perms):
    def _(ctx):
        me = ctx.guild.me if ctx.message.guild else ctx.bot.user
        for perm in perms:
            if not getattr(ctx.channel.permissions_for(me), perm):
                raise errors.CheckFailure("I need the %s permission" % perm)
        return True
    return commands.check(_)

def author_needs(perms):
    def _(ctx):
        author = ctx.message.author
        for perm in perms:
            if not getattr(ctx.channel.permissions_for(author), perm):
                raise errors.CheckFailure("You need the %s permission" % perm)
        return True
    return commands.check(_)

def is_owner():
    def _(ctx):
        if ctx.author.id != 474104220770107392:
            raise errors.CheckFailure("I don't think you can do that...")
        return True
    return commands.check(_)
