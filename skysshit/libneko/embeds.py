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
    Espy/Neko404NotFound
"""

__all__ = (
    "default_colour",
    "unspecified_field",
    "empty_field",
    "InvalidEmbedURL",
    "FieldIsTooLong",
    "EmbedIsTooLong",
    "Embed",
)

import typing
from datetime import datetime
from urllib import parse as urlparse

from discord import embeds
from discord.errors import ClientException

from libneko.singleton import Singleton

default_colour = 0x363940

#: Unused unicode character that shows up as nothing on Discord. Is used to hack
#: together empty embed fields, and whathaveyou.
empty_field = "\uFFF0"


class UnspecifiedField(Singleton):
    """
    Base type for an unspecified field sentinel marker object.

    You do not ever need to make instances of this class, or use it directly.
    Instead, you should use the :attr:``unspecified_field`` object.

    This exists purely to aid type checking.
    """

    def __bool__(self) -> bool:
        return False

    def __str__(self) -> str:
        return empty_field


#: Marks a field as unspecified
unspecified_field = UnspecifiedField()


class InvalidEmbedURL(ClientException):
    """Raised if an embed URL is deemed invalid."""

    def __init__(self, url, name, reason) -> None:
        self.url, self.name, self.reason = url, name, reason

    def __str__(self) -> str:
        return f'The {(self.name + " ").lstrip()}URL {self.url} is not valid because {self.reason}.'


class FieldIsTooLong(ClientException):
    """Raised if a field is too long."""

    def __init__(self, field_name, input_value, max_length) -> None:
        self.field_name, self.input_value, self.max_length = (field_name, input_value, max_length)

    def __str__(self) -> str:
        return (
            f"The field {self.field_name} has a max length of {self.max_length} but your "
            f"input was {len(self.input_value)} characters in size. The input was:"
            f"{self.input_value}"
        )


class EmbedIsTooLong(ClientException):
    """Raised if an embed is too long."""

    def __init__(self, actual_size, counted_type="characters", actual_limit=6000) -> None:
        self.actual_size = actual_size
        self.counted_type = counted_type
        self.actual_limit = actual_limit

    def __str__(self) -> str:
        return (
            f"Embeds are limited to {self.actual_limit} {self.counted_type}, you have "
            f"{self.actual_size} {self.counted_type}."
        )


# noinspection PyAttributeOutsideInit,PyRedeclaration
class Embed:
    """
    Reimplementation of Discord.py's Embed class.

    - The default colour is now more aesthetic, and can accept an RGB tuple in
      addition to the original options. The default colour is ``#363940`` which
      "doesn't show up" on dark mode, and looks rather nice.
    - Timestamp is added by default.
    - Fields are not inline by default, as generally people don't want inlined fields.
    - Fields can now have "empty" attributes without error-ing (achieved by adding an
      unused unicode value as the default placeholder).
    - Everything is validated client side, rather than relying on Discord to validate
      it for us. This is more efficient, gives better error messages, and is generally
      a more responsible thing to do (saves spamming Discord with bad requests, too).
    - URLs are validated client side too. This will not catch all bad input errors, but
      it should help vastly.
    - Image URLs have a custom proxy URL set now which directs to the original content,
      or can be optionally specified as something else. This appears to speed up content
      loading significantly in tests I have run.
    
    To disable the default timestamp, set the `timestamp` argument to None or False. If
    you set the `timestamp` to be `True`, then it will be set to the current UTC timestamp.
    This is the default behaviour.
    """

    __slots__ = (
        "_title",
        "_description",
        "_url",
        "_color",
        "_timestamp",
        "_thumbnail",
        "_image",
        "_author",
        "_footer",
        "_fields",
    )

    def __init__(
        self,
        *,
        title=unspecified_field,
        description=unspecified_field,
        colour=unspecified_field,
        color=unspecified_field,
        url=unspecified_field,
        timestamp=True,
    ) -> None:
        self._maybe_set("title", title)
        self._maybe_set("description", description)

        if color is unspecified_field and colour is unspecified_field:
            color = default_colour

        self._maybe_set("color", colour)
        self._maybe_set("color", color)
        self._maybe_set("url", url)

        if timestamp is True:
            timestamp = datetime.utcnow()
        elif timestamp is False or timestamp is None:
            timestamp = unspecified_field

        self._maybe_set("timestamp", timestamp)

        self._fields = []

    @property
    def type(self) -> str:
        """Returns the string `rich`."""
        return "rich"

    @type.setter
    def type(self, value) -> "typing.NoReturn":
        raise NotImplementedError(
            "Only `rich` is allowed as a type, which is the default anyway, "
            "so this feature is disabled until further notice. You have no "
            "real reason to be touching it."
        )

    @property
    def title(self) -> typing.Union[UnspecifiedField, str]:
        """Returns the title, or :attr:`unspecified_field` if unspecified."""
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        if value is not unspecified_field and len(str(value)) > 256:
            raise FieldIsTooLong("title", value, 256)

        self._title = value

    @property
    def description(self) -> typing.Union[UnspecifiedField, str]:
        """Returns the description, or :attr:`unspecified_field` if unspecified."""
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        if value is not unspecified_field and len(str(value)) > 2048:
            raise FieldIsTooLong("description", value, 2048)

        self._description = value

    @property
    def url(self) -> typing.Union[UnspecifiedField, str]:
        """Returns the URL, or :attr:`unspecified_field` if unspecified."""
        return self._url

    @url.setter
    def url(self, value) -> None:
        if value is not unspecified_field:
            self._validate_url(value, "url")
        self._url = value

    @property
    def colour(self) -> typing.Union[UnspecifiedField, embeds.Colour]:
        """Gets the colour of this embed. If unspecified, it reverts to the default colour."""
        return self._color

    @colour.setter
    def colour(self, colour) -> None:
        if isinstance(colour, tuple):
            red, green, blue = colour

            if not (0 <= red < 256):
                raise ValueError("Red channel must be in range [0,256)")
            elif not (0 <= green < 256):
                raise ValueError("Green channel must be in range [0,256)")
            elif not (0 <= blue < 256):
                raise ValueError("Blue channel must be in range [0,256)")
            else:
                colour = red << 16 | green << 8 | blue
        elif isinstance(colour, str):
            if colour.startswith("#"):
                colour = colour[1:]

            colour = int(colour, 16) & 0xFFFFFF
        elif isinstance(colour, UnspecifiedField):
            colour = default_colour
        elif isinstance(colour, embeds.Colour):
            self._color = colour
            return

        self._color = embeds.Colour(colour)

    #: Alias for :attr:`color` for the 'muricans.
    color = colour

    @property
    def timestamp(self) -> typing.Union[UnspecifiedField, datetime]:
        """Returns the UTC timestamp, or :attr:`unspecified_field` if unspecified."""
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value) -> None:
        if not isinstance(value, (datetime, UnspecifiedField)):
            raise TypeError(f"Expected `datetime` timestamp, got {type(value).__qualname__}")
        else:
            self._timestamp = value

    @property
    def fields(self) -> typing.List[dict]:
        """Returns the list of fields, or :attr:`unspecified_field` if unspecified."""
        return self._fields

    def add_field(self, *, name: str = None, value: str = None, inline: bool = False) -> "Embed":
        """
        Adds the given field.

        This WILL allow "empty" values now. Additionally, fields are not inline
        unless you explicitly specify that they should be.

        Returns a reference to this object to allow chaining.
        """
        if name is None:
            name = empty_field
        else:
            name = str(name)

        if value is None:
            value = empty_field
        else:
            value = str(value)

        if len(name.strip()) > 256:
            raise FieldIsTooLong("field.name", name, 256)
        elif len(name.strip()) == 0:
            name = unspecified_field

        if len(value.strip()) > 1024:
            raise FieldIsTooLong("field.value", value, 1024)
        elif len(value.strip()) == 0:
            value = unspecified_field

        if len(self.fields) >= 24:
            raise EmbedIsTooLong(len(self.fields), "fields", 24)

        self._fields.append(dict(name=name, value=value, inline=inline))

        return self

    def set_field_at(
        self, index: int, *, name: str = None, value: str = None, inline: bool = False
    ) -> "Embed":
        """
        Sets the field at the given index.

        Returns a reference to this object to allow for chaining.
        """
        if index < 0:
            raise ValueError("Index cannot be less than 0")
        if index > 24:
            raise ValueError("Index cannot be greater than 24")

        if name is None:
            name = empty_field
        else:
            name = str(name)

        if value is None:
            value = empty_field
        else:
            value = str(value)

        if len(name.strip()) > 256:
            raise FieldIsTooLong("field.name", name, 256)
        elif len(name.strip()) == 0:
            name = unspecified_field

        if len(value.strip()) > 1024:
            raise FieldIsTooLong("field.value", value, 1024)
        elif len(value.strip()) == 0:
            value = unspecified_field

        if len(self.fields) > 24:
            raise EmbedIsTooLong(len(self.fields), "fields", 24)

        self._fields[index] = dict(name=name, value=value, inline=inline)

        return self

    @property
    def image(self) -> typing.Union[UnspecifiedField, dict]:
        """
        Returns the dict representing the image, or :attr:`unspecified_field` if unspecified.
        """
        return self._image

    def set_image(self, *, url: str, proxy_url: str = empty_field) -> "Embed":
        """
        Sets the image with the URL. Uses this for the proxy, additionally, if one isn't specified.
        """
        if proxy_url is empty_field:
            proxy_url = url
        else:
            self._validate_url(proxy_url, "image.proxy_url")

        if url is empty_field:
            url = proxy_url
        else:
            self._validate_url(url, "image.url")

        self._image = {"url": url, "proxy_url": proxy_url}

        return self

    @property
    def thumbnail(self) -> typing.Union[UnspecifiedField, dict]:
        """
        Returns the dict representing the thumbnail, or :attr:`unspecified_field` if unspecified.
        """
        return self._thumbnail

    def set_thumbnail(self, *, url: str, proxy_url: str = empty_field) -> "Embed":
        """
        Sets the thumbnail image with the URL. Uses this for the proxy, additionally, if one isn't
        specified.
        """
        if proxy_url is empty_field:
            proxy_url = url
        else:
            self._validate_url(proxy_url, "thumbnail.proxy_url")

        if url is empty_field:
            url = proxy_url
        else:
            self._validate_url(url, "thumbnail.url")

        self._thumbnail = {"url": url, "proxy_url": proxy_url}

        return self

    @property
    def footer(self) -> typing.Union[UnspecifiedField, dict]:
        """
        Returns the footer, or :attr:`unspecified_field` if unspecified.
        """
        return self._footer

    def set_footer(
        self, *, text: str = unspecified_field, icon_url: str = unspecified_field
    ) -> "Embed":
        """
        Sets the footer; returns a reference to this object to allow for chaining.
        """
        if icon_url is not unspecified_field:
            self._validate_url(icon_url, "footer.icon_url")

        if isinstance(text, str):
            if len(text.strip()) == 0:
                text = empty_field
        if len(text) > 2048:
            raise FieldIsTooLong("footer.text", text, 2048)

        self._footer = dict(text=text, icon_url=icon_url)
        return self

    @property
    def author(self) -> typing.Union[UnspecifiedField, dict]:
        """
        Returns the author, or :attr:`unspecified_field` if unspecified.
        """
        return self._author

    def set_author(
        self, *, name: str, url: str = unspecified_field, icon_url: str = unspecified_field
    ) -> "Embed":
        """
        Sets the author; returns a reference to this object to allow for chaining.
        """
        if url is not unspecified_field:
            self._validate_url(url, "author.url")

        if icon_url is not unspecified_field:
            self._validate_url(icon_url, "author.icon_url")

        name = str(name)
        if not name.strip():
            name = empty_field
        elif len(name) > 256:
            raise FieldIsTooLong("author.name", name, 256)

        self._author = dict(name=name, url=url, icon_url=icon_url)
        return self

    def _key_inclusion_predicate(self, name):
        return (
            name[0] == "_" and hasattr(self, name) and getattr(self, name) is not unspecified_field
        )

    @classmethod
    def _recursively_scrub_in_place(cls, d):
        """Removes any fields marked as unspecified_field recursively in place"""
        # Shallow copy to allow us to modify in-place.
        for k, v in {**d}.items():
            if isinstance(v, dict):
                d[k] = cls._recursively_scrub_in_place(v)
            elif v is unspecified_field:
                # Remove field altogether.
                d.pop(k)

        return d

    def to_dict(self) -> dict:
        """
        Converts this embed object into a dict. Used by Discord.py internally to
        enable compatibility with the existing :class:`discord.Embed` class.

        This addresses #11 properly this time.
        """

        # add in the raw data into the dict
        result = self._recursively_scrub_in_place(
            {
                key[1:]: getattr(self, key)
                for key in self.__slots__
                if self._key_inclusion_predicate(key)
            }
        )

        # deal with basic convenience wrappers
        if "color" in result:
            result["color"] = self._color.value

        try:
            timestamp = result.pop("timestamp")
        except KeyError:
            pass
        else:
            if timestamp:
                result["timestamp"] = timestamp.isoformat()

        return result

    def _maybe_set(self, field: str, value: typing.Any) -> None:
        """Used internally to only store a field reference if it is specified."""
        if value is not unspecified_field:
            setattr(self, field, value)

    @staticmethod
    def _validate_url(url, name="url") -> None:
        """
        Internal helper that validates a URL. If it is valid, nothing happens.
        If we cannot parse it correctly, then an InvalidEmbedURL is raised instead
        containing some info.
        """
        try:
            urlparse.urlparse(url)
        except Exception as ex:
            raise InvalidEmbedURL(url, name, ex)
