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
Custom converter classes. These are compatible with the type checker used in
IDEs such as PyCharm, so you should not get any issues with unresolved attributes
any more!

Author:
    Espy/Neko404NotFound
"""

__all__ = (
    "CommandConverter",
    "CogConverter",
    "GuildChannelCategoryConverter",
    "GuildChannelConverter",
    "LowercaseCategoryConverter",
    "InsensitiveCategoryConverter",
    "MentionConverter",
    "MentionOrSnowflakeConverter",
    "BoolConverter",
    "IntConverter",
    "FloatConverter",
    "DecimalConverter",
    "Converter",
    "MemberConverter",
    "UserConverter",
    "InviteConverter",
    "RoleConverter",
    "GameConverter",
    "ColourConverter",
    "EmojiConverter",
    "InsensitiveUserConverter",
    "InsensitiveMemberConverter",
)

import decimal
import re
import typing

import discord
from discord.ext import commands as _commands
from discord.ext.commands.converter import (
    Converter,
    MemberConverter,
    UserConverter,
    InviteConverter,
    RoleConverter,
    GameConverter,
    ColourConverter,
    EmojiConverter,
)

from libneko import funcmods

if typing.TYPE_CHECKING:

    class CommandConverter(_commands.Command):
        async def convert(self, ctx, argument):
            ...


else:

    class CommandConverter(_commands.Converter):
        """Takes a fully qualified command name and returns the command object, if it exists."""

        async def convert(self, ctx, argument):
            c = ctx.bot.get_command(argument)
            if not c:
                raise _commands.BadArgument(f"Command `{argument}` was not found")
            else:
                return c


if typing.TYPE_CHECKING:

    class CogConverter(object):
        async def convert(self, ctx, argument):
            ...


else:

    class CogConverter(_commands.Converter):
        """Takes a cog name and returns the cog, if it exists and is loaded."""

        async def convert(self, ctx, argument):
            try:
                return ctx.bot.cogs[argument]
            except KeyError as ex:
                raise _commands.BadArgument(f"{ex} was not loaded.")


if typing.TYPE_CHECKING:

    class GuildChannelConverter:
        async def convert(self, ctx, argument):
            ...


else:

    class GuildChannelConverter(_commands.Converter):
        """
        Gets a guild channel
        """

        async def convert(self, ctx, body: str):
            for t in (_commands.TextChannelConverter, _commands.VoiceChannelConverter):
                try:
                    return await t().convert(ctx, body)
                except Exception:
                    pass

            raise _commands.BadArgument(f"No channel matching `{body}` was found.")


if typing.TYPE_CHECKING:

    class InsensitiveCategoryConverter(str):
        async def convert(self, ctx, argument):
            ...


else:

    class InsensitiveCategoryConverter(_commands.Converter):
        """
        Gets a category case insensitive. Discord doesn't show the name in the
        case the name is stored in; instead, it is transformed to uppercase. This
        makes this whole thing kind of useless to the user unless they can guess
        the correct permutation of character cases that was used.
        """

        async def convert(self, ctx, argument):
            argument = argument.lower()

            for category in ctx.guild.categories:
                if category.name.lower() == argument:
                    return category

            raise _commands.BadArgument(f"Category matching `{argument}` was not " "found.")


#: Deprecated alias for :class:`InsensitiveCategoryConverter`\.
LowercaseCategoryConverter = InsensitiveCategoryConverter

if typing.TYPE_CHECKING:

    class GuildChannelCategoryConverter(discord.CategoryChannel):
        async def convert(self, ctx, argument):
            ...


else:

    class GuildChannelCategoryConverter(_commands.Converter):
        """
        Gets a guild channel or category.
        """

        async def convert(self, ctx, body: str):
            # If the input is in the format <#123> then it is a text channel.
            if body.startswith("<#") and body.endswith(">"):
                sf_str = body[2:-1]
                if sf_str.isdigit():
                    sf = int(sf_str)
                    channel = discord.utils.find(lambda c: c.id == sf, ctx.guild.channels)

                    if channel:
                        return channel

                raise _commands.BadArgument(
                    "Unable to access that channel. Make "
                    "sure that it exists, and that I have "
                    "access to it, and try again."
                )

            # Otherwise, it could be a text channel, a category or a voice channel.
            # We need to hunt for it manually.
            else:
                to_search = {*ctx.guild.channels, *ctx.guild.categories}
                channel = discord.utils.find(lambda c: c.name == body, to_search)
                if channel:
                    return channel

                # Attempt case insensitive searching
                body = body.lower()
                channel = discord.utils.find(lambda c: c.name.lower() == body, to_search)
                if channel:
                    return channel
                raise _commands.BadArgument("No channel matching input was found.")


if typing.TYPE_CHECKING:

    class MentionConverter(object):
        async def convert(self, ctx, argument):
            ...


else:

    class MentionConverter(_commands.Converter):
        """
        A converter that takes generic types of mentions.
        """

        async def convert(self, ctx, body: str):
            if body.startswith("<") and body.endswith(">"):
                tb = body[1:-1]

                if tb.startswith("@&"):
                    return await _commands.RoleConverter().convert(ctx, body)
                elif tb.startswith("@") and tb[1:2].isdigit() or tb[1:2] == "!":
                    return await _commands.MemberConverter().convert(ctx, body)
                elif tb.startswith("#"):
                    return await _commands.TextChannelConverter().convert(ctx, body)
            else:
                try:
                    return await _commands.EmojiConverter().convert(ctx, body)
                except Exception:
                    pass

                try:
                    return await GuildChannelCategoryConverter().convert(ctx, body)
                except Exception:
                    pass

                try:
                    return await _commands.PartialEmojiConverter().convert(ctx, body)
                except Exception:
                    pass

            # Attempt to find in whatever we can look in. Don't bother looking
            # outside this guild though, as I plan to keep data between guilds
            # separate for privacy reasons.

            if ctx.guild:
                all_strings = [
                    *ctx.guild.members,
                    *ctx.guild.channels,
                    *ctx.guild.categories,
                    *ctx.guild.roles,
                    *ctx.guild.emojis,
                ]

                def search(obj):
                    if getattr(obj, "display_name", "") == body:
                        return True
                    if str(obj) == body or obj.name == body:
                        return True
                    return False

                # Match case first, as a role and member, say, may share the same
                # name barr the case difference, and this could lead to unwanted
                # or unexpected results. The issue is this will get slower as a
                # server gets larger, generally.
                result = discord.utils.find(search, all_strings)
                if not result:
                    # Try again not matching case.
                    def search(obj):
                        _body = body.lower()

                        if getattr(obj, "display_name", "").lower() == _body:
                            return True
                        if str(obj).lower() == _body:
                            return True
                        if obj.name.lower() == _body:
                            return True
                        return False

                    result = discord.utils.find(search, all_strings)

                if not result:
                    raise _commands.BadArgument(f"Could not resolve `{body}`")
                else:
                    return result


if typing.TYPE_CHECKING:

    class MentionOrSnowflakeConverter:
        async def convert(self, ctx, argument):
            ...


else:

    class MentionOrSnowflakeConverter(MentionConverter):
        """
        A specialisation of MentionConverter that ensures that raw snowflakes can
        also be input. This returns the string if nothing was resolved.
        """

        async def convert(self, ctx, body: str):
            if body.isdigit():
                return int(body)
            else:
                try:
                    return await super().convert(ctx, body)
                except _commands.BadArgument:
                    return body


#################################################################################
# Since the converters have been changed, this allows nicer validation with the #
# correct errors.                                                               #
#################################################################################


if typing.TYPE_CHECKING:

    class BoolConverter(bool):
        async def convert(self, ctx, argument):
            ...


else:

    @funcmods.steal_docstring_from(_commands.Converter)
    class BoolConverter(_commands.Converter):
        """Converts to a boolean."""

        async def convert(self, ctx, argument):
            if not isinstance(argument, (int, str, bool)):
                raise _commands.BadArgument("Invalid boolean value")
            else:
                if isinstance(argument, str):
                    argument = argument.lower()

                try:
                    return {
                        "0": False,
                        0: False,
                        "false": False,
                        "f": False,
                        "n": False,
                        "no": False,
                        "nope": False,
                        "nah": False,
                        "negative": False,
                        "unset": False,
                        "disable": False,
                        "disabled": False,
                        "unenable": False,
                        "unenabled": False,
                        False: False,
                        "1": True,
                        1: True,
                        "true": True,
                        "t": True,
                        "y": True,
                        "yes": True,
                        "ok": True,
                        "positive": True,
                        "set": True,
                        "enable": True,
                        "enabled": True,
                        True: True,
                    }[argument]
                except KeyError:
                    raise _commands.BadArgument(
                        f"Did not recognise {argument} as a valid " "boolean argument"
                    )


if typing.TYPE_CHECKING:

    class IntConverter(int):
        async def convert(self, ctx, argument):
            ...


else:

    @funcmods.steal_docstring_from(_commands.Converter)
    class IntConverter(_commands.Converter):
        """Converts to an integer."""

        async def convert(self, ctx, argument):
            try:
                return int(argument)
            except Exception:
                raise _commands.BadArgument("Invalid integer value")


if typing.TYPE_CHECKING:

    class FloatConverter(float):
        async def convert(self, ctx, argument):
            ...


else:

    @funcmods.steal_docstring_from(_commands.Converter)
    class FloatConverter(_commands.Converter):
        """Converts to a float."""

        async def convert(self, ctx, argument):
            try:
                return float(argument)
            except Exception:
                raise _commands.BadArgument("Invalid float value")


if typing.TYPE_CHECKING:

    class DecimalConverter(decimal.Decimal):
        async def convert(self, ctx, argument):
            ...


else:

    @funcmods.steal_docstring_from(_commands.Converter)
    class DecimalConverter(_commands.Converter):
        """Converts to a multi-precision decimal."""

        async def convert(self, ctx, argument):
            try:
                return decimal.Decimal(argument)
            except Exception:
                raise _commands.BadArgument("Invalid integer value")


if typing.TYPE_CHECKING:

    # noinspection PyPep8Naming
    @funcmods.steal_docstring_from(_commands.clean_content)
    class clean_content(_commands.clean_content, str):
        pass


else:
    # noinspection PyPep8Naming
    @funcmods.steal_docstring_from(_commands.clean_content)
    class clean_content(_commands.clean_content):
        pass


# M.A. requested these.


if typing.TYPE_CHECKING:

    class InsensitiveUserConverter(discord.User):
        """
        Same as UserConverter, but this will fall back to attempting to match a user
        case insensitive if this fails before giving up.

        Procedure is as follows:
        1. Lookup using UserConverter
        2. Lookup using case insensitive username and discriminator
        3. Lookup using case insensitive username
        """

        async def convert(self, ctx, argument):
            ...


else:

    class InsensitiveUserConverter(_commands.Converter):
        """
        Same as UserConverter, but this will fall back to attempting to match a user
        case insensitive if this fails before giving up.

        Procedure is as follows:
        1. Lookup using UserConverter
        2. Lookup using case insensitive username and discriminator
        3. Lookup using case insensitive username
        4. Lookup using ID globally on Discord.
        """

        async def convert(self, ctx, argument):
            try:
                return await UserConverter().convert(ctx, argument)
            except _commands.BadArgument:

                def predicate_user_and_discriminator(user):
                    return (
                        user.name.lower() == argument[:-5].lower()
                        and str(user.discriminator) == argument[-4:]
                    )

                def predicate_user(user):
                    return user.name.lower() == argument.lower()

                result = None

                if len(argument) > 5 and argument[-5] == "#":
                    result = discord.utils.find(predicate_user_and_discriminator, ctx.bot.users)

                if result is None:
                    result = discord.utils.find(predicate_user, ctx.bot.users)

                if result is None:
                    try:
                        result = await ctx.bot.fetch_user(int(argument))
                    except Exception:
                        result = None

            if result is None:
                raise _commands.BadArgument('User "{}" not found'.format(argument))
            else:
                return result


if typing.TYPE_CHECKING:

    class InsensitiveMemberConverter(discord.User):
        """
        Same as MemberConverter, but this will fall back to attempting to match a user
        case insensitive if this fails before giving up.

        The procedure for this is as follows:

        1. Lookup using MemberConverter
        2. Lookup by ID
        3. Lookup by nickname insensitive
        4. Lookup by name#discrim insensitive
        5. Lookup by name insensitive
        6. Lookup by nick insensitive
        """

        async def convert(self, ctx, argument):
            ...


else:

    class InsensitiveMemberConverter(_commands.Converter):
        """
        Same as MemberConverter, but this will fall back to attempting to match a user
        case insensitive if this fails before giving up.

        The procedure for this is as follows:

        1. Lookup using MemberConverter
        2. Lookup by ID
        3. Lookup by nickname insensitive
        4. Lookup by name#discrim insensitive
        5. Lookup by name insensitive
        6. Lookup by nick insensitive
        """

        async def convert(self, ctx, argument):
            if not ctx.guild:
                return await UserConverter().convert(ctx, argument)

            try:
                return await MemberConverter().convert(ctx, argument)
            except _commands.BadArgument:
                if argument.isdigit():
                    try:
                        return await ctx.bot.fetch_user(int(argument))
                    except discord.NotFound:
                        pass
                else:
                    id_matcher = re.match(r"<@!?(\d+)>", argument)
                    if id_matcher:
                        id = int(id_matcher.group(1))
                        try:
                            return await ctx.bot.fetch_user(id)
                        except discord.NotFound:
                            pass

                def predicate_user_and_discriminator(user):
                    return (
                        user.name.lower() == argument[:-5].lower()
                        and str(user.discriminator) == argument[-4:]
                    )

                search_pool = [*ctx.guild.members, *ctx.bot.users]

                def predicate_user(user):
                    return user.name.lower() == argument.lower()

                def predicate_nick(user):
                    return getattr(user, "nick", None) and user.nick.lower() == argument.lower()

                result = None

                if len(argument) > 5 and argument[-5] == "#":
                    result = discord.utils.find(predicate_user_and_discriminator, search_pool)

                if result is None:
                    result = discord.utils.find(predicate_user, search_pool)

                if result is None:
                    result = discord.utils.find(predicate_nick, search_pool)

            if result is None:
                raise _commands.BadArgument('User "{}" not found'.format(argument))
            else:
                return result
