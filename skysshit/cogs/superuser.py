import ast
import asyncio
import collections
import contextlib
import copy
import importlib
import io
import logging
import os
import pprint
import re
import shutil
import sys
import time
import traceback
from discord.ext import commands
from libneko import commands
from libneko.pag import factory
import discord

_logger = logging.getLogger("libneko.extras.superuser")



class SuperuserCog(commands.Cog):
   def __init__(self, bot):
        self.bot = bot
   
   @commands.command(name="exec", aliases=["shell", "eval", "sh"], hidden=True)
   async def execute(self, ctx, *, code):
        """Executes the given code."""

        # Removes code blocks if they are present. This then captures the
        # syntax highlighting to use if it is present.
        code_block = re.findall(r"```([a-zA-Z0-9]*)\s([\s\S(^\\`{3})]*?)\s*```", code)

        if code_block:
            lang, code = code_block[0][0], code_block[0][1]

            if lang in ("py", "python", "python3", "python3.6", "python3.7"):
                lang = "python"
        else:
            if ctx.invoked_with in ("exec", "eval"):
                lang = "python"
            elif self.shell is None:
                return await ctx.send(
                    "This feature has been disabled by the bot owner.", delete_after=15
                )
            else:
                lang = self.shell

        executor = execute_in_session if lang == "python" else execute_in_shell

        additional_messages = []

        async with ctx.typing():
            # Allows us to capture any messages the exec sends, and we can delete
            # them with the paginator later.
            hooked_ctx = copy.copy(ctx)

            async def send(*args, **kwargs):
                m = await ctx.send(*args, **kwargs)
                additional_messages.append(m)
                return m

            hooked_ctx.send = send

            sout, serr, result, exec_time, prog = await executor(hooked_ctx, lang, code)

        pag = factory.StringNavigatorFactory(
            prefix="```diff\n",
            suffix="```",
            max_lines=25,
            enable_truncation=False,
            substitutions=[scrub],
        )

        nl = "\n"
        pag.add_line(f'---- {prog.replace(nl, " ")} ----')

        if sout:
            pag.add_line("- /dev/stdout:")
            for line in sout.split("\n"):
                pag.add_line(line)
        if serr:
            pag.add_line("- /dev/stderr:")
            for line in serr.split("\n"):
                pag.add_line(line)
        if len(str(result)) > 100:
            pag.add_line(f"+ Took approx {1000 * exec_time:,.2f}ms; returned:")
            for p in pprint.pformat(result, indent=4).split("\n"):
                pag.add_line(p)
        else:
            pag.add_line(f"+ Returned `{result}` in approx {1000 * exec_time:,.2f}ms. ")

        nav = pag.build(ctx)
        nav.start()
        await nav.is_ready.wait()
        commands.reinvoke_on_edit(ctx, *nav.all_messages, *additional_messages)

@commands.command(hidden=True)
async def panic(self, ctx):
        """Panic mode. Unloads this cog, specifically."""
        ctx.bot.remove_cog(ctx.cog)

        try:
            await ctx.message.delete()
        except Exception:
            pass

        await ctx.send("Exec cog has been deactivated.", delete_after=10)



def setup(bot):
    """Add the cog to the bot directly. Enables this to be loaded as an extension."""
    bot.add_cog(SuperuserCog(bot))
