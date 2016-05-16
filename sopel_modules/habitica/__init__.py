# -*- coding: utf8 -*-

from __future__ import absolute_import

import sopel.module

from .common import set_up
from .chat import read_chat, say_chat
from .hero import hero_command


def setup(bot):
    set_up(bot)


@sopel.module.rate(60)
@sopel.module.commands('hero')
def hero(bot, trigger):
    hero_command(bot, trigger)


@sopel.module.commands('say')
def say(bot, trigger):
    say_chat(bot, trigger)


@sopel.module.priority("low")
@sopel.module.interval(60)
def chat(bot):
    read_chat(bot)
