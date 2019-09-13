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
Custom checks you can use with commands.

Note:
    This is designed to be used as a replacement for any checks in
    :mod:`discord.ext.commands.core`.

Author:
    Espy/Neko404NotFound
"""

__all__ = (
    "NotGuildOwner",
    "is_guild_owner",
    "check",
    "is_owner",
    "bot_has_role",
    "bot_has_any_role",
    "bot_has_permissions",
    "guild_only",
    "is_nsfw",
    "cooldown",
    "has_any_role",
    "has_role",
    "has_permissions",
    "BucketType",
)

from discord.ext import commands as _commands
from discord.ext.commands import bot_has_role, guild_only, cooldown, has_any_role, has_role
from discord.ext.commands import check, is_owner, is_nsfw, bot_has_any_role, bot_has_permissions
from discord.ext.commands import has_permissions, BucketType


class NotGuildOwner(_commands.CheckFailure):
    """
    Raised if a command decorated with the ``@is_guild_owner()`` check is invoked by
    someone other than the guild owner.
    """

    def __init__(self):
        super().__init__("You are not the server owner, so you cannot run this command.")


def is_guild_owner():
    """
    A check returning true if the guild owner invoked the command, and we are in a guild.

    If we are not in a guild, we return False to fail the check. If we are not the guild
    owner, and one exists, we raise ``NotGuildOwner`` to show a custom error message.
    """

    def decorator(ctx):
        if not ctx.guild:
            return False
        elif not (ctx.guild.owner.id == ctx.author.id or ctx.author.id == ctx.bot.owner_id):
            raise NotGuildOwner
        return True

    return check(decorator)
