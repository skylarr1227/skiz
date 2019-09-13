#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# MIT License
#
# Copyright (c) 2018-2019 Flitt3r (a.k.a Koyagami)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in a$
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
An extension that can be loaded for providing a customisable exec command.

Author:
    Espy/Neko404NotFound
"""
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

import aiofiles
import aiohttp
import discord

from libneko import commands
from libneko.pag import factory

_logger = logging.getLogger("libneko.extras.superuser")


def maybe_import(lib):
    try:
        module = importlib.import_module(lib)
        _logger.debug("Successfully loaded %s", lib)
        return module
    except Exception as ex:
        _logger.debug("Failed to load %s because %s: %s", lib, type(ex).__qualname__, str(ex))
        return None


class _ModuleDict(collections.OrderedDict):
    """Used internally to make """

    def __str__(self):
        k: str
        return f"ModuleDict({{{','.join(str(k) for k in self.keys())}}})"

    __repr__ = __str__


#: Modules to inject into global scope for python exec calls.
modules = _ModuleDict(
    aiohttp=maybe_import("aiohttp"),
    async_timeout=maybe_import("async_timeout"),
    asyncio=maybe_import("asyncio"),
    collections=maybe_import("collections"),
    commands=maybe_import("libneko.commands"),
    dataclasses=maybe_import("dataclasses"),
    decimal=maybe_import("decimal"),
    discord=maybe_import("discord"),
    functools=maybe_import("functools"),
    hashlib=maybe_import("hashlib"),
    inspect=maybe_import("inspect"),
    io=maybe_import("io"),
    json=maybe_import("json"),
    libneko=maybe_import("libneko"),
    math=maybe_import("math"),
    os=maybe_import("os"),
    random=maybe_import("random"),
    re=maybe_import("re"),
    requests=maybe_import("requests"),
    statistics=maybe_import("statistics"),
    sys=maybe_import("sys"),
    textwrap=maybe_import("textwrap"),
    urllib=maybe_import("urllib"),
    urlparse=maybe_import("urllib.parse"),
    weakref=maybe_import("weakref"),
    bs4=maybe_import("bs4"),
    subprocess=maybe_import("subprocess"),
    time=maybe_import("time"),
    datetime=maybe_import("datetime"),
)


# noinspection PyUnresolvedReferences
async def execute_in_session(ctx, program, code):
    """|coro|

    Executes the given code in the current interpreter session.

    Arguments:
        ctx:
            the command invocation context. This is used to get a reference to the bot
            which is injected into scope when ``exec``ing the contents of ``code``.
        program:
            the program name. This is unused for this implementation.
        code:
            the raw source code to execute.

    Warning:
        This method provides no user validation or verification. Unless you implement
        it yourself, it will allow anyone to use it. Consider using the cog for a
        working safer implementation.

    Returns:
        A 4-tuple containing stdout (string), stderr (string), the exit code (int) and the
        time taken to run the command (float).

    """
    sout = io.StringIO()
    serr = io.StringIO()

    nl = "\n"

    # Redirect all streams.
    with contextlib.redirect_stdout(sout):
        with contextlib.redirect_stderr(serr):

            start_time = float("nan")

            # noinspection PyBroadException
            try:
                # Intrinsics to eval the line where possible if it is one line.
                # This will implicitly cause the result of await expressions to be
                # awaited, which is cool. Downside of this is we have to compile twice.

                try:
                    abstract_syntax_tree = ast.parse(
                        code, filename=f"{ctx.guild}{ctx.channel.mention}.py"
                    )

                    node: list = abstract_syntax_tree.body

                    # If we have an expr node as the root, automatically append on a
                    # call to return to implicitly return the expr'ed value.
                    if node and type(node[0]) is ast.Expr:
                        code = f"return " + code.strip()

                except Exception:
                    pass

                func = (
                    "async def aexec(ctx, bot):\n"
                    f'{nl.join(((" " * 4) + line) for line in code.split(nl))}'
                )

                start_time = time.monotonic()
                exec(func, modules, locals())

                result = await locals()["aexec"](ctx, ctx.bot)
                if hasattr(result, "__await__"):
                    print(f"Returned awaitable {result}. Awaiting it.", file=sys.stderr)
                    result = await result
            except BaseException as ex:
                traceback.print_exc()
                result = type(ex)
            finally:
                exec_time = time.monotonic() - start_time

    return (
        sout.getvalue(),
        serr.getvalue(),
        result,
        exec_time,
        f'Python {sys.version.replace(nl, " ")}',
    )


# noinspection PyUnusedLocal
async def execute_in_shell(ctx, program, code):
    """|coro|

    Executes the given code in a separate process, using the given program as an interpreter.

    Arguments:
        ctx:
            the command invocation context. Unused.
        program:
            the program name. This will be resolved by the OS by traversing any directories in
            the current working directory, and the ``PATH`` environment variable. This may
            alternatively be an absolute path to an executable.
        code:
            the raw source code to execute.

    Warning:
        This method provides no user validation or verification. Unless you implement
        it yourself, it will allow anyone to use it. Consider using the cog for a
        working safer implementation.

    Returns:
            A 4-tuple containing stdout (string), stderr (string), the exit code (int) and the
            time taken to run the command (float).
    """

    path = shutil.which(program)
    if not path:
        return "", f"{program} not found.", 127, 0.0, ""

    start_time = time.monotonic()
    process = await asyncio.create_subprocess_exec(
        path,
        "--",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE,
    )

    sout, serr = await process.communicate(bytes(code, "utf-8"))
    exec_time = time.monotonic() - start_time

    exit_code = process.returncode

    sout = sout.decode()
    serr = serr.decode()

    return sout, serr, str(exit_code), exec_time, path


def scrub(content):
    """Replaces triple back ticks with triple grave accents."""
    return content.replace("\N{GRAVE ACCENT}" * 3, "\N{MODIFIER LETTER GRAVE ACCENT}" * 3)


class SuperuserCog(commands.Cog):
    # noinspection PyUnresolvedReferences
    """
    Parameters:
        shell: The default shell to use. If not overridden, it will use the best shell as
            determined for the target platform. If ``None``, then the shell is disabled.
            Otherwise, it should be an absolute path to an executable, or an executable that
            is accessible via the ``$PATH`` variable.

    Note:
        This includes a command called ``panic`` which removes this command
        from the bot until it is reloaded again.

        >>> [you] %panic
        >>> [bot] Exec cog has been deactivated.

    Warning:
        This cog poses an inherent security risk on your bot if not implemented correctly.
        It relies on Discord IDs always being valid and never spoofed. If compromised,
        the attacker is able to execute any arbitrary code on your host. Depending on the bot's
        system user account permissions, this could be used to perform potentially devastating
        raid attacks and system compromise. **Use at your own risk.**
    """

    def __init__(self, *, shell=...):
        if shell is ...:
            self.shell = os.getenv(
                "SHELL", os.name in ("win32", "win64", "winnt", "nt") and "cmd" or "bash"
            )
        elif shell is None:
            self.shell = None
        else:
            self.shell = shell

    async def cog_check(self, ctx):
        """
        Checks the owner is valid. If no owner is set, it should immediately fail.

        This defaults to ensuring an owner is the owner of the bot account.

        This class can be inherited, and you can override this method to do basically
        what the hell you want to though... take the following example that demonstrates
        using a hard-coded list of members to allow access to this cog::

            >>> from libneko.extras import superuser

            >>> class WhitelistedOwnerSuperuserCog(superuser.SuperuserCog):
            ...
            ...     owners = [1856271517491511531, 4325824835683126527, 21512642468346835632]
            ...     async def owner_check(self, ctx):
            ...         return ctx.author.id in self.owners
            ...

            >>> bot.add_cog(WhitelistedOwnerSuperuserCog())

        """
        return await ctx.bot.is_owner(ctx.author)

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

    @commands.group()
    async def wget(self, ctx):
        await commands.send_usage(ctx)

    @wget.command()
    async def down(self, ctx, *, path):
        try:
            async with aiofiles.open(path, "wb") as fp:
                async with aiohttp.request("get", ctx.message.attachments[0].url) as r:
                    r.raise_for_status()
                    await fp.write(await r.read())
        except IndexError:
            await ctx.send("Please provide an attachment...")
        except Exception as ex:
            await ctx.send(f"{type(ex).__name__} {ex}")
        else:
            await ctx.send("Saved...", delete_after=10)

    @wget.command()
    async def up(self, ctx, *, path):
        try:
            await ctx.author.send(file=discord.File(path))
        except Exception as ex:
            await ctx.send(f"{type(ex).__name__} {ex}")
        else:
            await ctx.send("Check your DMs", delete_after=15)


def setup(bot):
    """Add the cog to the bot directly. Enables this to be loaded as an extension."""
    bot.add_cog(SuperuserCog())
