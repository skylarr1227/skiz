#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from libneko.embeds import *


class DictifyMixin:
    def __init__(self, *args, **kwargs):
        self.i = 0
        try:
            super().__init__(*args, **kwargs)
        except TypeError:
            super().__init__()

    def run(self, *args, **kwargs):
        self.i = 0
        return super().run(*args, **kwargs)

    def _dictify(self, embed):
        self.i += 1
        with self.subTest(f"toDict subtest {self.i}"):
            d = embed.to_dict()
            self.assertIsInstance(d, dict)
            self._assert_members_are_jsonifyable_recursive(d)
            return d

    def _assert_members_are_jsonifyable_recursive(self, o, nest=0):
        if isinstance(o, list):
            for m in o:
                self._assert_members_are_jsonifyable_recursive(m, nest + 1)
        elif isinstance(o, dict):
            for k, v in o.items():
                self.assertIsInstance(k, str, f"Expected key to be str in nested level {nest}")
                self._assert_members_are_jsonifyable_recursive(v, nest + 1)
        else:
            none_type = type(None)
            if not isinstance(o, (none_type, int, float, str, bool, type(unspecified_field))):
                self.fail(f"{o} in nest level {nest} is not JSONifyable.")


class EmbedLimitsTest(DictifyMixin, unittest.TestCase):
    def test_nothing(self):
        self._dictify(Embed())

    def test_title(self):
        self._dictify(Embed(title=""))  # Should be valid.
        self._dictify(Embed(title="x" * 255))  # Should be valid.
        self._dictify(Embed(title="x" * 256))  # Should be valid.

        with self.assertRaises(FieldIsTooLong):
            Embed(title="x" * 257)

    def test_description(self):
        self._dictify(Embed(description=""))  # Should be valid.
        self._dictify(Embed(description="x" * 2047))  # Should be valid.
        self._dictify(Embed(description="x" * 2048))  # Should be valid.

        with self.assertRaises(FieldIsTooLong):
            Embed(description="x" * 2049)

    def test_field_name(self):
        empty_dict = self._dictify(Embed().add_field(name=""))  # Should be valid.
        self.assertEqual(empty_field, str(empty_dict["fields"][0]["name"]))
        empty_dict = self._dictify(Embed().add_field(name="          "))  # Should be valid.
        self.assertEqual(empty_field, str(empty_dict["fields"][0]["name"]))

        self._dictify(Embed().add_field(name="x" * 255))  # Should be valid.
        self._dictify(Embed().add_field(name="x" * 256))  # Should be valid.

        with self.assertRaises(FieldIsTooLong):
            Embed().add_field(name="x" * 257)

    def test_field_value(self):
        empty_dict = self._dictify(Embed().add_field(value=""))  # Should be valid.
        self.assertEqual(empty_field, str(empty_dict["fields"][0]["value"]))
        empty_dict = self._dictify(Embed().add_field(value="          "))  # Should be valid.
        self.assertEqual(empty_field, str(empty_dict["fields"][0]["value"]))

        self._dictify(Embed().add_field(value="x" * 1023))  # Should be valid.
        self._dictify(Embed().add_field(value="x" * 1024))  # Should be valid.

        with self.assertRaises(FieldIsTooLong):
            Embed().add_field(value="x" * 1025)

    def test_author_name(self):
        self._dictify(Embed().set_author(name=""))  # Should be valid.
        self._dictify(Embed().set_author(name="x" * 255))  # Should be valid.
        self._dictify(Embed().set_author(name="x" * 256))  # Should be valid.

        with self.assertRaises(FieldIsTooLong):
            Embed().set_author(name="x" * 257)

    def test_footer_text(self):
        self._dictify(Embed().set_footer(text=""))  # Should be valid.
        self._dictify(Embed().set_footer(text="x" * 2047))  # Should be valid.
        self._dictify(Embed().set_footer(text="x" * 2048))  # Should be valid.

        with self.assertRaises(FieldIsTooLong):
            Embed().set_footer(text="x" * 2049)

    def test_field_count(self):
        e = Embed()

        # Should be fine
        for i in range(23):
            e.add_field(name=str(i), value=str(i))

        # Should also be fine
        e.add_field(name="Last valid field", value="before we have too many")

        self._dictify(e)

        with self.assertRaises(EmbedIsTooLong):
            self.assertEqual(24, len(e.fields))
            e.add_field(name="Too many", value="This should now raise.")


class EmbedURLTest(DictifyMixin, unittest.TestCase):
    def test_url(self):
        e = Embed()
        e.url = "http://google.com"  # Should be valid.
        self._dictify(e)

        with self.assertRaises(InvalidEmbedURL):
            Embed().url = 22

    def test_image_url(self):
        e = Embed().set_image(url="http://google.com")  # Should be valid.
        self._dictify(e)
        with self.assertRaises(InvalidEmbedURL):
            Embed().set_image(url=22)

    def test_thumbnail_url(self):
        e = Embed().set_thumbnail(url="http://google.com")  # Should be valid.
        self._dictify(e)
        with self.assertRaises(InvalidEmbedURL):
            Embed().set_thumbnail(url=22)

    def test_author_url(self):
        e = Embed().set_author(name="foobar", url="http://google.com")  # Should be valid.
        self._dictify(e)
        with self.assertRaises(InvalidEmbedURL):
            Embed().set_author(name="foobar", url=22)

    def test_author_icon_url(self):
        e = Embed().set_author(name="foobar", icon_url="http://google.com")  # Should be valid.
        self._dictify(e)

        with self.assertRaises(InvalidEmbedURL):
            Embed().set_author(name="foobar", icon_url=22)

    def test_footer_icon_url(self):
        e = Embed().set_footer(text="foobar", icon_url="http://google.com")  # Should be valid.
        self._dictify(e)

        with self.assertRaises(InvalidEmbedURL):
            Embed().set_footer(text="foobar", icon_url=22)


class EmbedRGBTest(DictifyMixin, unittest.TestCase):
    def test_rgb_conversion(self):
        for r in range(200, 203):
            for g in range(33, 66):  # 256 takes too long, and the logic is the same.
                for b in range(3, 10):
                    hex_str = f"0x{r:>02x}{g:>02x}{b:>02x}"
                    hex_int = int(hex_str, 16)
                    tuple = (r, g, b)

                    e1 = Embed(colour=tuple)
                    e2 = Embed(color=tuple)

                    self.assertEqual(hex_int, e1.colour.value, str(tuple))
                    self.assertEqual(hex_int, e1.color.value, str(tuple))

                    self.assertEqual(hex_int, e2.colour.value, str(tuple))
                    self.assertEqual(hex_int, e2.color.value, str(tuple))

    def test_range(self):
        # Base cases that should not error
        self._dictify(Embed(colour=(0, 30, 30)))
        self._dictify(Embed(colour=(30, 0, 30)))
        self._dictify(Embed(colour=(30, 30, 0)))
        self._dictify(Embed(colour=(255, 30, 30)))
        self._dictify(Embed(colour=(30, 255, 30)))
        self._dictify(Embed(colour=(30, 30, 255)))

        with self.assertRaises(ValueError):
            Embed(colour=(-1, 30, 30))
        with self.assertRaises(ValueError):
            Embed(colour=(30, -1, 30))
        with self.assertRaises(ValueError):
            Embed(colour=(30, 30, -1))
        with self.assertRaises(ValueError):
            Embed(colour=(256, 30, 30))
        with self.assertRaises(ValueError):
            Embed(colour=(30, 256, 30))
        with self.assertRaises(ValueError):
            Embed(colour=(30, 30, 256))
