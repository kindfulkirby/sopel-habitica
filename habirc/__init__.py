# -*- coding: utf8 -*-

from __future__ import absolute_import

import sopel.module

from .common import Common, set_up
from .chat import read_chat
from .status import show_status


def setup(bot):
    set_up(bot)


@sopel.module.commands('status')
def status(bot, trigger):
    show_status(bot, trigger)


@sopel.module.interval(60)
def chat(bot):
    read_chat(bot)
