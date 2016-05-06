# -*- coding: utf8 -*-

from __future__ import absolute_import

import re

from sopel.config.types import StaticSection, ValidatedAttribute, ListAttribute


class HabircSection(StaticSection):
    api_user = ValidatedAttribute('api_user')
    api_key = ValidatedAttribute('api_key')
    max_messages = ValidatedAttribute('max_messages', int, default=3)
    channels = ListAttribute('channels')


class Common:
    """ Provides static variables and methods common to several submodules,"""

    auth = {}
    last_timestamp = {}
    uuid_regex = re.compile(ur'[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}')


def get_name_colors(user):
    """
    :param user: The dict of a Habitica user, as returned from the API
    :return: A tuple of the fore- and background color belonging to the user's class
    """
    colors = {
        0: ("white", "grey"),
        1: ("white", "pink"),
        2: ("white", "brown"),
        3: ("white", "red"),
        4: ("white", "orange"),
        5: ("black", "yellow"),
        6: ("black", "green"),
        7: ("black", "cyan"),
        8: ("white", "blue"),
        9: ("white", "purple"),
        10: ("green", "black")
    }

    level = 0

    if "level" in user["contributor"]:
        level = user["contributor"]["level"]

    if "npc" in user["backer"]:
        level = 10

    return colors[level]


def set_up(bot):
    bot.config.define_section('habirc', HabircSection)

    Common.auth = {"x-api-key": bot.config.habirc.api_key, "x-api-user": bot.config.habirc.api_user}

    for channel in bot.config.habirc.channels:
        timestamp = bot.db.get_channel_value(channel, "last_timestamp")
        if timestamp is None:
            Common.last_timestamp[channel] = 0
        else:
            Common.last_timestamp[channel] = int(timestamp)
