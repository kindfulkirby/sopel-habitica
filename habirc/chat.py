# -*- coding: utf8 -*-

from __future__ import absolute_import

import requests
from sopel.formatting import color

from .common import Common, get_name_colors


def read_chat(bot):
    chat = requests.get("https://habitica.com/api/v2/groups/habitrpg/chat", headers=Common.auth)

    if chat.status_code != 200:
        return

    for channel in bot.config.habirc.channels:

        if channel in bot.channels:

            for line in xrange(30, -1, -1):

                timestamp = int(chat.json()[line]["timestamp"])

                if timestamp <= Common.last_timestamp[channel]:
                    continue

                uuid = chat.json()[line]["uuid"]

                if uuid == "system":
                    bot.msg(channel, color(chat.json()[line]["text"][1:-1], "pink"))
                else:
                    user = requests.get("https://habitica.com/api/v2/members/" + uuid, headers=Common.auth)

                    name = " " + user.json()["profile"]["name"] + " "
                    colors = get_name_colors(user.json())
                    message = chat.json()[line]["text"]
                    bot.msg(channel, color(name, colors[0], colors[1]) + " " + message,
                            max_messages=bot.config.habirc.max_messages)

            Common.last_timestamp[channel] = int(chat.json()[0]["timestamp"])
            bot.db.set_channel_value(channel, "last_timestamp", Common.last_timestamp[channel])
