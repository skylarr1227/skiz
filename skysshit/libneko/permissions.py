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
Author:
    Neko404NotFound/Espy
"""

__all__ = ("Permissions",)

import enum
import typing

import discord


class Permissions(enum.IntFlag):
    """
    Danny's Permissions class does not define these as integer constants. We
    can define these as follows which allows for bitwise or-ing the values
    to combine permissions.

    There is an additional utility method to convert to the Discord.py variant
    included here for ease of use.

    Because of how enums work, and how Discord.py works, this should work as
    a fully functioning drop-in without any modification.

    Example::

        >>> role = ...
        >>> await role.edit(permissions=Permissions.MANAGE_MESSAGES | Permissions.EMBED_LINKS)

    Casting to :class:`discord.Permissions`::

        >>> import libneko, discord
        >>> perms = libneko.Permissions.MANAGE_MESSAGES | libneko.Permissions.EMBED_LINKS
        >>> perms = discord.Permissions(perms)

    Casting from :class:`discord.Permissions`::

        >>> import libneko, discord
        >>> perms = discord.Permissions.all_channel()
        >>> perms = libneko.Permissions(perms)

    Iterating across each permission::

        >>> perms = Permissions.all_channel()
        >>> for name in perms:
        ...     print(name)
        KICK_MEMBERS
        BAN_MEMBERS
        MANAGE_GUILD
        ADMINISTRATOR
        CHANGE_NICKNAMES
        MANAGE_NICKNAMES

    """

    NONE = 0x00000000
    CREATE_INSTANT_INVITE = 0x00000001
    KICK_MEMBERS = 0x00000002
    BAN_MEMBERS = 0x00000004
    ADMINISTRATOR = 0x00000008
    MANAGE_CHANNELS = 0x00000010
    MANAGE_GUILD = 0x00000020
    ADD_REACTIONS = 0x00000040
    VIEW_AUDIT_LOG = 0x00000080
    # Deprecated 1 = 0x00000100
    # Deprecated 2 = 0x00000200
    READ_MESSAGES = 0x00000400
    SEND_MESSAGES = 0x00000800
    SEND_TTS_MESSAGES = 0x00001000
    MANAGE_MESSAGES = 0x00002000
    EMBED_LINKS = 0x00004000
    ATTACH_FILES = 0x00008000
    READ_MESSAGE_HISTORY = 0x00010000
    MENTION_EVERYONE = 0x00020000
    USE_EXTERNAL_EMOJIS = 0x00040000
    # Deprecated 3 = 0x00080000
    CONNECT = 0x00100000
    SPEAK = 0x00200000
    MUTE_MEMBERS = 0x00400000
    DEAFEN_MEMBERS = 0x00800000
    MOVE_MEMBERS = 0x01000000
    USE_VAD = 0x02000000
    CHANGE_NICKNAME = 0x04000000
    MANAGE_NICKNAMES = 0x08000000
    MANAGE_ROLES = 0x10000000
    MANAGE_WEBHOOKS = 0x20000000
    MANAGE_EMOJIS = 0x40000000

    def __new__(cls, value):
        if isinstance(value, discord.Permissions):
            value = value.value
        return super().__new__(cls, value)

    def __iter__(self):
        for name, value in type(self).__members__.items():
            if value & self:
                yield name, bool(value)

    def _iter_bitwise(self):
        for name, value in type(self).__members__.items():
            yield name, value

    def unmask(self) -> typing.List[typing.Tuple[str, int]]:
        """
        Takes a masked set of permissions and returns each set bit as a string
        of the corresponding permission names in a list.
        """
        return [p for p in self._iter_bitwise()]

    ############################################################################
    # Taken from discord.py's Permissions class to aid in compatibility.       #
    ############################################################################

    @classmethod
    def none(cls):
        """A factory method that creates a :class:`Permissions` with all
        permissions set to False."""
        return cls(0b00000000000000000000000000000000)

    @classmethod
    def all(cls):
        """A factory method that creates a :class:`Permissions` with all
        permissions set to True."""
        return cls(0b01111111111101111111110011111111)

    @classmethod
    def all_channel(cls):
        """A :class:`Permissions` with all channel-specific permissions set to
        True and the guild-specific ones set to False. The guild-specific
        permissions are currently:

        - manage_guild
        - kick_members
        - ban_members
        - administrator
        - change_nicknames
        - manage_nicknames
        """
        return cls(0b00110011111101111111110001010001)

    @classmethod
    def general(cls):
        """A factory method that creates a :class:`Permissions` with all
        "General" permissions from the official Discord UI set to True."""
        return cls(0b01111100000000000000000010111111)

    @classmethod
    def text(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Text" permissions from the official Discord UI set to True."""
        return cls(0b00000000000001111111110001000000)

    @classmethod
    def voice(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Voice" permissions from the official Discord UI set to True."""
        return cls(0b00000011111100000000000000000000)
