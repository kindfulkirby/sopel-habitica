# -*- coding: utf8 -*-

from __future__ import absolute_import

import re

from sopel.config.types import StaticSection, ValidatedAttribute, ListAttribute


class HabiticaSection(StaticSection):
    api_user = ValidatedAttribute('api_user')
    api_key = ValidatedAttribute('api_key')
    max_lines = ValidatedAttribute('max_lines', int, default=5)
    channels = ListAttribute('channels')
    chats = ListAttribute('chats')
    colors = ValidatedAttribute('colors', bool, default=True)
    api_url = ValidatedAttribute('api_url', default="https://habitica.com/api/v2/")

# noinspection PyClassHasNoInit
class Common:
    """ Provides static variables common to several submodules,"""

    auth = {}
    chats = {}
    uuid_regex = re.compile(ur'[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}')
    code_tag_regex = re.compile(ur'(`[^`]+`)')
    name_prefix = " "
    name_suffix = " "
    default_colors = ("white", "grey")
    hp_color = "red"
    mp_color = "blue"
    xp_color = "yellow"
    gp_color = "olive"
    action_color = "pink"
    user_colors = {
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


def get_name_colors(user):
    """
    :param user: The dict of a Habitica user, as returned from the API
    :return: A tuple of the fore- and background color belonging to the user's class
    """

    level = 0

    if "level" in user["contributor"]:
        level = user["contributor"]["level"]

    if "npc" in user["backer"]:
        level = 10

    return Common.user_colors[level]


def set_up(bot):
    bot.config.define_section('habitica', HabiticaSection)

    Common.auth = {"x-api-key": bot.config.habitica.api_key, "x-api-user": bot.config.habitica.api_user}

    if len(bot.config.habitica.channels) != len(bot.config.habitica.chats):
        raise ValueError("Length of configured channels and chats do not match.")

    Common.chats = dict(zip(bot.config.habitica.channels, bot.config.habitica.chats))

    if not bot.config.habitica.colors:
        Common.name_prefix = "["
        Common.name_suffix = "]"
        Common.default_colors = (None, None)
        Common.hp_color = None
        Common.mp_color = None
        Common.xp_color = None
        Common.gp_color = None
        Common.action_color = None
        Common.user_colors = {
            0: (None, None),
            1: (None, None),
            2: (None, None),
            3: (None, None),
            4: (None, None),
            5: (None, None),
            6: (None, None),
            7: (None, None),
            8: (None, None),
            9: (None, None),
            10: (None, None),
        }

    bot.memory["habitica_last_timestamp"] = dict()
    bot.memory["habitica_read_chat_lock"] = False

    for channel in bot.config.habitica.channels:
        timestamp = bot.db.get_channel_value(channel, "habitica_last_timestamp")
        if timestamp is None:
            bot.memory["habitica_last_timestamp"][channel] = 0
        else:
            bot.memory["habitica_last_timestamp"][channel] = int(timestamp)
