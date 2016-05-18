# -*- coding: utf8 -*-

from __future__ import absolute_import

from time import sleep

import requests
from sopel.formatting import color

from .common import Common, get_name_colors


def parse_code_tags(bot, text):
    if not bot.config.habitica.colors:
        return text

    result = ""

    segments = Common.code_tag_regex.split(text)

    #filter out zero-length segments
    segments = filter(None, segments)

    for segment in segments:
        if segment[0] == "`" and segment[-1] == "`":
            result += color(segment[1:-1], Common.action_color)
        else:
            result += segment

    return result


def send_message(bot, channel, message):
    uuid = message["uuid"]

    if uuid == "system":
        name = "*"
        colors = (Common.action_color, None)

    else:
        user = requests.get(bot.config.habitica.api_url + "members/" + uuid, headers=Common.auth)

        if user.status_code == 200:
            name = Common.name_prefix + user.json()["profile"]["name"] + Common.name_suffix
            colors = get_name_colors(user.json())

        else:
            name = Common.name_prefix + message["user"] + Common.name_suffix
            colors = Common.default_colors

    text = parse_code_tags(bot, message["text"])

    bot.msg(
        channel,
        color(name, colors[0], colors[1]) + " " + text,
        max_messages=bot.config.habitica.max_lines
    )

    # manual rate limiting, otherwise multi-line messages might be broken up due to bot's scheduling
    sleep(len(text) / 400.0)


def read_chat(bot):
    if bot.memory["habitica_read_chat_lock"]:
        return

    bot.memory["habitica_read_chat_lock"] = True

    for channel in bot.config.habitica.channels:

        if channel not in bot.channels:
            continue

        chat = Common.chats[channel]

        if chat.upper() == "NONE":
            continue

        lines = requests.get(bot.config.habitica.api_url + "groups/" + chat + "/chat", headers=Common.auth)

        if lines.status_code != 200:
            continue

        for line in reversed(lines.json()):

            timestamp = int(line["timestamp"])

            if timestamp <= bot.memory["habitica_last_timestamp"][channel]:
                continue

            bot.memory["habitica_last_timestamp"][channel] = timestamp

            # weird messages sometimes show up, containing only "."; we ignore these.
            if line["text"] == ".":
                continue

            send_message(bot, channel, line)

        bot.db.set_channel_value(channel, "habitica_last_timestamp", bot.memory["habitica_last_timestamp"][channel])

    bot.memory["habitica_read_chat_lock"] = False


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
            bot.config.habitica.api_url + "groups/" + chat + "/chat",
            headers=headers,
            params=payload
        )

        if response.status_code != 200:
            bot.say("No connection to Habitica. Please try again later.")

        read_chat(bot)

    else:
        bot.reply("Please use me in a channel that has a Habitica chat associated with it.")