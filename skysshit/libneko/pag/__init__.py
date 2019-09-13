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
Utilities for paginating arbitrary content such as strings, in order to fit
inside a message in Discord.

This also has utilities to enable the creation of a navigation-like object in
a Discord chat. This is a state machine that contains a certain page from a 
paginator, and provides Discord reactions (known as "buttons") that have
actions associated with them. When an authorised user (fully customisable) 
interacts with said reaction, the bot will remove the reaction and perform the
given task. This enables navigation through paginator output while only
displaying one message at a time. Buttons are easily created and can do anything
you desire within the constraints of Discord.py.
"""

from .abc import *
from .factory.basefactory import *
from .factory.embedfactory import *
from .factory.stringfactory import *
from .navigator import *
from .optionpicker import *
from .paginator import *
from .reactionbuttons import *
