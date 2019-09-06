import discord
from discord.ext import commands
import textwrap


class Show(commands.Cog):

    @commands.group(invoke_without_command=True, name='show', case_insensitive=True)
    @commands.cooldown(3, 2, commands.BucketType.user)
    async def show(self, ctx, val=None):
        if val is not None:
            val = val.lower()
        if val is None:
            embed = discord.Embed(title="Skybot Useful Information", description="use any of the below subcommands with +show to show information on different catagories", color=0x0084FD)
            embed.add_field(name="shortcuts", value="``+show shortcuts`` -  Custom defined shortcuts for long/hard to remember commands", inline=False)
            embed.add_field(name="leveler", value="``+show leveler`` -  Information on how to use the chat leveling module", inline=False)
            embed.add_field(name="Admin/Server owner commands", value="``adminhelp`` - helpful stuff for server owners and admins", inline=False)
           # embed.add_field(name="Gear Overview", value="``r.help gear`` - See commands that give you details about your character's gear.", inline=False)
          #  embed.add_field(name="Info Overview", value="``r.help info`` - See commands that give you character/item information.", inline=False)
          #  embed.add_field(name="Extra Commands", value="``r.help extras`` - See commands for status, leaderboards, etc.", inline=False)
            #embed.set_thumbnail(url='https://i.imgur.com/7W9FXN1.png')
            await ctx.send(embed=embed)

    @show.command()
    async def shortcuts(self, ctx):
        embed = discord.Embed(title="Command Shortcuts", description="Custom shortcuts to make long/difficult commands easier (Always growing list, will try to update often) feel free to send suggestions in dm to the bot, they do get checked.", color=0x0084FD)
        embed.add_field(name="will add soon", value="``will add soon``", inline=False)
        embed.add_field(name="Work in progress", value="will add soon")
        await ctx.send(embed=embed)

    @show.command()
    async def leveler(self, ctx):
        embed = discord.Embed(title="Skybot Chat Leveling User Guide", description="Gain experience by sending messages anywhere, there are cooldowns in place and minimum length requirements to make abusing this module harder.", color=0x0084FD)
        embed.add_field(name="User Profile Configuration", value="``+lvlset profile`` -  Change your displayed bg/title/about", inline=False)
        embed.add_field(name="User Rank Page Configuration", value="``+lvlset rank bg <name of bg>`` -  Change rank page bg (background name)  ", inline=False)
        embed.add_field(name="User LeveUP Display Background", value="``+lvlset levelup bg <bg name>`` - Change your level up bg (background name).", inline=False)
        embed.add_field(name="View Available Backgrounds", value="``+backgrounds profile | rank | levelup`` -  Use displayed name for the background", inline=False)
        await ctx.send(embed=embed)    
    
   # @help.command()
   # async def shop(self, ctx):
      #  embed = discord.Embed(title="RealmBot Store Help", description="Help with store options, ``r.store`` also works in place of ``r.shop``.", color=0x0084FD)
      #  embed.add_field(name="Character Shop", value="``r.shop char`` - Different summoning options for new characters!", inline=False)
      #  embed.add_field(name="Weapon Shop", value="``r.shop weapons`` - Different weapon choices for each class!", inline=False)
      #  embed.add_field(name="Armor Shop", value="``r.shop armor`` - Different armor choices for physical or magical classes!", inline=False)
       # embed.add_field(name="Accessory Shop", value="``r.shop accs`` - Different accessory choices for every class!", inline=False)
      #  await ctx.send(embed=embed)

    #@help.command()
  #  async def gear(self,ctx):
  #      embed = discord.Embed(title="RealmBot Gear Help", description="Help with gear options.", color=0x0084FD)
  #      embed.add_field(name="Character Gear Display", value="``r.gear`` or ``r.gear (char's num)``\nWithout character input it shows default character's gear.", inline=False)
   #     embed.add_field(name="Gear Equipping", value="``r.equip (char's num) (gear ID)``\nFirst number is the character's number, 2nd number is the item's ID which can be found with ``r.items``.", inline=False)
      #  embed.add_field(name="Gear Unequipping", value="``r.unequip (char's num) (gear ID)``\nFirst number is the character's number, 2nd number is the item's ID which can be found with ``r.items``.", inline=False)
    #    await ctx.send(embed=embed)

  #  @help.command()
#    async def info(self,ctx):
 #       embed = discord.Embed(title="RealmBot Info Help", description="Help with the different type of info commands available", color=0x0084FD)
 #       embed.add_field(name="Base Info Command", value="``r.base (type) (name)``\nBase character or item portfolios.\n**Examples**:\n``r.base info ushan`` - Shows Ushan's base information\n``r.base item wooden sword`` - Shows wooden sword's base information.", inline=False)
 #       embed.add_field(name="Info Command", value="``r.info (char's number)``\nThis if for looking at attribute points on your character.", inline=False)
     #   embed.add_field(name="Stats Command", value="``r.info (char's number)``\n This is for looking at your character's stats, like attack power.", inline=False)
    #    await ctx.send(embed=embed)

 #   @help.command()
   # async def extras(self, ctx):            
 #       embed = discord.Embed(title="RealmBot Park Commands", description="Commands that show details about your park, rides, and other details.", color=0x0084FD)
  #      embed.add_field(name="Status", value="``r.status`` - Shows bot details.", inline=False)
  #      embed.add_field(name="Income", value="``r.invite`` - Shows an invite for the bot and Official server.", inline=False)
  #      await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Show(bot))
