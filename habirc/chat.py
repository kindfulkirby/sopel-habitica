# -*- coding: utf8 -*-

from __future__ import absolute_import

import requests
from sopel.formatting import color

from .common import Common, get_name_colors


def post_message(bot, channel, message):
    uuid = message["uuid"]

    if uuid == "system":
        bot.msg(channel, color(message["text"][1:-1], "pink"))

    else:
        user = requests.get("https://habitica.com/api/v2/members/" + uuid, headers=Common.auth)

        if user.status_code == 200:
            name = " " + user.json()["profile"]["name"] + " "
            colors = get_name_colors(user.json())

        else:
            name = " " + message["user"] + " "
            colors = ("white", "grey")

        text = message["text"]

        bot.msg(
            channel,
            color(name, colors[0], colors[1]) + " " + text,
            max_messages=bot.config.habirc.max_messages
        )


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

        for line in xrange(bot.config.habirc.chat_lines, -1, -1):

            timestamp = int(lines.json()[line]["timestamp"])

            if timestamp <= Common.last_timestamp[channel]:
                continue

            message = lines.json()[line]

            post_message(bot, channel, message)

        Common.last_timestamp[channel] = int(lines.json()[0]["timestamp"])
        bot.db.set_channel_value(channel, "last_timestamp", Common.last_timestamp[channel])


def say_chat(bot, trigger):
    channel = trigger.sender

    if channel in bot.channels and not trigger.is_privmsg:

        api_user = bot.db.get_nick_value(trigger.nick, 'habitica_api_user')
        api_key = bot.db.get_nick_value(trigger.nick, 'habitica_api_key')

        if api_user is None:
            bot.reply("I do not know you, sorry. Please use '.hero add'.")
            return

        else:
            if api_key is None:
                bot.reply("I cannot send messages for you without your API Token. Please use '.hero key'.")
                return
            else:
                headers = {"x-api-key": api_key, "x-api-user": api_user}

        chat = Common.chats[channel]

        if chat.upper() == "NONE":
            return

        payload = {"message": trigger.group(2)}

        response = requests.post(
            "https://habitica.com/api/v2/groups/" + chat + "/chat",
            headers=headers,
            params=payload
        )

        if response.status_code != 200:
            bot.say("No connection to Habitica. Please try again later.")

        message = response.json()["message"]

        post_message(bot, channel, message)

    else:
        bot.reply("Please use me in a channel that has a Habitica chat associated with it.")