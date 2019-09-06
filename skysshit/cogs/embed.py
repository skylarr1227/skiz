import discord
import os
import asyncio
from discord.message import *
from discord.ext.commands import Bot
#from discord.ext.commands import ConversionError #remembered what I was going to use it for: find the error raised if not enough inputs are inputted for embed command, prevent txt file (substitute for db file) from being written in so it doesn't store faulty data and break everything
from discord.ext import commands

#client = Bot
path = ''

class Embed(commands.Cog):
    def __init__(self, bot):
        #client = Bot
		
@commands.command(name = "embed",
                brief = "Does embedding.",
                aliases = ["e"],
                description = "Embeds guilds for Dream's sake. Note 'embedDesc' is optional. Requires permission 'manage_messages' to be used.",
                pass_context = True)
@commands.has_permissions(manage_messages = True)
async def embed(ctx, sendToChannel: discord.TextChannel, embedTitle, embedInvite, embedImage, gwCode, embedDesc = None):
    embed = discord.Embed(color = 0x36393E)
    embed.set_image(url = embedImage)
    embed.add_field(name = "Guild Name", value = embedTitle, inline = True)
    embed.add_field(name = "Link", value = embedInvite, inline = True)
    
    if embedDesc != None:
        embed.add_field(name = "Description", value = embedDesc, inline = False)

    newSpace = "\n"

    newPath = (path + embedTitle + ".txt")

    pathCheck = os.path.isfile(newPath)

    if pathCheck == True:
        await ctx.channel.send("Path already exists. Pick another name or delete the file.")
    elif pathCheck == False:
        open(path + embedTitle + ".txt", 'x')
        print(newPath)

        embedFile = open(newPath, 'w')
        embedFile.write("Guild Name: " + embedTitle + newSpace)
        embedFile.write("Invite Link: " + "<" + embedInvite + ">" + newSpace)
        embedFile.write("GW Code: " + gwCode.lower() + newSpace)
        embedFile.write(embedImage + newSpace)

        if embedDesc != None:
            embedFile.write("Desc: " + embedDesc)
        embedFile.close()
    
    await client.get_channel(sendToChannel.id).send(embed = embed)

@commands.command(hidden = True,
                pass_context = True) #pass needed so I can use ctx
@commands.has_permissions(manage_messages = True)
async def cleardb(ctx, flag = None):
    if flag == None:
        await ctx.channel.send("Clearing all data...")
        for bdir, dirs, files in os.walk(path):
            for fname in files:
                print(bdir, fname)
                os.remove(path + fname)
        await ctx.channel.send("Done.")
    elif flag != None:
        await ctx.channel.send("Clearing specific file...")
        os.remove(path + flag + ".txt")
        await ctx.channel.send("Done.")

@commands.command(hidden = True,
                pass_context = True)
@commands.has_permissions(manage_messages = True)
async def listdb(ctx):
    for bdir, dirs, files in os.walk(path):
        for fname in files:
            if fname.endswith(".txt"):
                fname = fname[:-4]
                await ctx.channel.send(fname) #fname being file name

@commands.command(pass_context = True)
async def search(ctx, fileName):
    pathCheck = os.path.isfile(path + fileName + ".txt")
    checkCount = 0
    errorCount = 0
    if pathCheck == True:
        await ctx.channel.send((open(path + fileName + ".txt", 'r').read()))
    elif pathCheck == False:
        for bdir, dirs, files in os.walk(path):
                for fname in files:
                    codeCheck = open(path + fname)
                    #print("1") these are all debug prints, kinda like laps. if it prints the number, shows me how far it got before looping back
                    for lineNum, linePrint in enumerate(codeCheck):
                        #print("2")
                        if lineNum == 2:
                            #print("3")
                            if fileName.lower() in linePrint:
                                checkCount += 1
                                if checkCount > 0:
                                    await ctx.channel.send((open((path + fname), 'r').read()))
                                    await asyncio.sleep(0.5) #prevent rate limiting (i think it's 5 inputs per like, 0.5s?)
                            elif fileName.lower() not in linePrint:
                                errorCount += 1
                                if errorCount == len(files):
                                    await ctx.channel.send("Invalid file name/GW code.")
									
									
									def setup(bot):
										bot.add_cog(Embed(bot))
    
