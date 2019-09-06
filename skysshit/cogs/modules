class Modules(commands.Cog):
    def __init__(self, bot):
    self.bot = bot
print('Addon "{}" loaded'.format(self.__class__.__name__))

@commands.group(hidden = True)
@is_owner()
async def module(self, ctx):
    if ctx.invoked_subcommand is None:
    await ctx.send(embed = Embed(title = "Module Commands", color = 0x9b006f,
        description = f "There are actually 3 Commands to use.\n "
        f "All Commands in this Group are Bot-Owner only!\n\n"
        f "{ctx.prefix}module load <ModuleName> || "
        f "Loads a Module\n"
        f "{ctx.prefix}module unload <ModuleName> || "
        f "Unloads a Module\n"
        f "{ctx.prefix}module load <ModuleName> || "
        f "Reloads a Module"))

@module.command()
async def load(self, ctx, *, cog: str):
    ""
"Load a Module."
""
try:
self.bot.load_extension(f 'modules.{cog}')
except Exception as e:
    await ctx.send(embed = Embed(description = '**`ERROR:`** {} - {}'.format(type(e).__name__, e)))
else :
    await ctx.send(embed = Embed(title = f '\u2705 **`SUCCESS`**: Addon "{str.title(cog)}" loaded',
        colour = 0x187E03))

@module.command()
async def unload(self, ctx, *, cog: str):
    ""
"Unload a Module."
""
try:
self.bot.unload_extension(f 'modules.{cog}')
except Exception as e:
    await ctx.send(embed = Embed(description = '**`ERROR:`** {} - {}'.format(type(e).__name__, e)))
else :
    await ctx.send(embed = Embed(title = f '\u2705 **`SUCCESS`**: Addon "{str.title(cog)}" unloaded',
        colour = 0x187E03))

@module.command()
async def reload(self, ctx, *, cog: str):
    ""
"Reload a Module."
""
try:
self.bot.unload_extension(f 'modules.{cog}')
self.bot.load_extension(f 'modules.{cog}')
except Exception as e:
    await ctx.send(embed = Embed(description = '**`ERROR:`** {} - {}'.format(type(e).__name__, e)))
else :
    await ctx.send(embed = Embed(title = f '\u2705 **`SUCCESS`**: Addon "{str.title(cog)}" '
        f 'reloaded', colour = 0x187E03))

def setup(bot):
    bot.add_cog(Modules(bot))
