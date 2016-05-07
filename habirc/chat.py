# -*- coding: utf8 -*-

from __future__ import absolute_import

import requests
from sopel.formatting import color

from .common import Common, get_name_colors


def read_chat(bot):
    for channel in bot.config.habirc.channels:

        if channel not in bot.channels:
            continue

        chat = Common.chats[channel]

        if chat.upper() == "NONE":
            continue

        lines = requests.get("https://habitica.com/api/v2/groups/" + chat + "/chat", headers=Common.auth)

        if lines.status_code != 200:
            continue

        for line in xrange(30, -1, -1):

            timestamp = int(lines.json()[line]["timestamp"])

            if timestamp <= Common.last_timestamp[channel]:
                continue

            uuid = lines.json()[line]["uuid"]

            if uuid == "system":
                bot.msg(channel, color(lines.json()[line]["text"][1:-1], "pink"))
            else:
                user = requests.get("https://habitica.com/api/v2/members/" + uuid, headers=Common.auth)

                if lines.status_code == 200:
                    name = " " + user.json()["profile"]["name"] + " "
                    colors = get_name_colors(user.json())

                else:
                    name = " " + lines.json()[line]["user"] + " "
                    colors = ("white", "grey")

                message = lines.json()[line]["text"]

                bot.msg(channel, color(name, colors[0], colors[1]) + " " + message,
                        max_messages=bot.config.habirc.max_messages)

        Common.last_timestamp[channel] = int(lines.json()[0]["timestamp"])
        bot.db.set_channel_value(channel, "last_timestamp", Common.last_timestamp[channel])
