# -*- coding: utf8 -*-

from __future__ import absolute_import

import requests
import re

import sopel.module
from sopel.config.types import StaticSection, ValidatedAttribute, ListAttribute
from sopel.formatting import color, bold


class HabIRC:
    auth = {}
    last_timestamp = {}
    api_regex = re.compile(ur'[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}')


class HabircSection(StaticSection):
    wait_time = ValidatedAttribute('wait_time', int, default=60)
    api_user = ValidatedAttribute('api_user')
    api_key = ValidatedAttribute('api_key')
    channels = ListAttribute('channels')


def setup(bot):
    bot.config.define_section('habirc', HabircSection)

    HabIRC.auth = {"x-api-key": bot.config.habirc.api_key, "x-api-user": bot.config.habirc.api_user}

    for channel in bot.config.habirc.channels:
        last_timestamp = bot.db.get_channel_value(channel, "last_timestamp")
        if last_timestamp is None:
            HabIRC.last_timestamp[channel] = 0
        else:
            HabIRC.last_timestamp[channel] = int(last_timestamp)


@sopel.module.commands('status')
def status_command(bot, trigger):
    """Replies with the configured character's status (HP, MP, XP & Gold)"""

    args = [trigger.group(3), trigger.group(4), trigger.group(5)]

    if args[0] == "add":
        start_configuration(bot, trigger)

    elif args[0] == "del":
        del_user(bot, trigger)

    elif args[0] == "user" and args[1] is not None:
        add_user(args, bot, trigger)

    elif args[0] == "user" and args[1] is None:
        info_user(bot, trigger)

    elif (args[0] == "key" and args[1] != "DANGER") or \
            (args[0] == "key" and args[1] == "DANGER" and args[2] is None):
        info_key(bot, trigger)

    elif args[0] == "key" and args[1] == "DANGER" and args[2] is not None:
        add_key(args, bot, trigger)

    elif args[0] is None:
        show_status(bot, trigger)

    else:
        bot.reply("Unknown command")


def show_status(bot, trigger):
    api_user = bot.db.get_nick_value(trigger.nick, 'habitica_api_user')
    api_key = bot.db.get_nick_value(trigger.nick, 'habitica_api_key')

    if api_user is None:
        bot.reply("I do not know you, sorry. Please use '.status add'.")
        return

    else:
        if api_key is None:
            user = requests.get("https://habitica.com/api/v2/members/" + api_user, headers=HabIRC.auth)
        else:
            headers = {"x-api-key": api_key, "x-api-user": api_user}
            user = requests.get("https://habitica.com/api/v2/user", headers=headers)

    if user.status_code != 200:
        bot.say("No connection to Habitica. Please try again later.")
        return

    hp = str(round(user.json()["stats"]["hp"], 2))
    mp = str(int(user.json()["stats"]["mp"]))
    gp = str(round(user.json()["stats"]["gp"], 2))
    xp = str(int(user.json()["stats"]["exp"]))
    name = user.json()["profile"]["name"]
    name_colors = get_name_colors(user.json())

    if api_key is not None:
        max_hp = user.json()["stats"]["maxHealth"]
        max_mp = user.json()["stats"]["maxMP"]
        to_next_level = user.json()["stats"]["toNextLevel"]

        hp = hp + "/" + str(max_hp)
        mp = mp + "/" + str(max_mp)
        xp = xp + "/" + str(to_next_level)

    sep = " | "

    bot.say("Status for "
            + color(" " + name + " ", name_colors[0], name_colors[1]) + " "
            + color(bold(u"♥ ") + hp + " HP", "red") + sep
            + color(bold(u"⚡ ") + mp + " MP", "blue") + sep
            + color(bold(u"⭐ ") + xp + " XP", "yellow") + sep
            + color(bold(u"⛁ ") + gp + " Gold", "olive")
    )


def get_name_colors(user):
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


def add_user(args, bot, trigger):
    if trigger.is_privmsg:
        user_id = HabIRC.api_regex.findall(args[1])

        if len(user_id) > 0:
            user_id = user_id[0]
        else:
            bot.msg(trigger.nick, "Invalid user ID")
            return

        bot.db.set_nick_value(trigger.nick, 'habitica_api_user', user_id)

        user = requests.get("https://habitica.com/api/v2/members/" + user_id, headers=HabIRC.auth)
        name = user.json()["profile"]["name"]

        bot.msg(trigger.nick, "Saved your character " + name)
        bot.msg(trigger.nick, "If you ever want to delete your settings, use '.status del'")
        bot.msg(trigger.nick, "If you want more details or use me to cast spells or use potions, you can " +
                "optionally add your API Token.")
        bot.msg(trigger.nick, "If you want this bot to save your API Token, add it with '.status key'")

    else:
        bot.reply("Please do not configure me in a public channel!")


def add_key(args, bot, trigger):
    if trigger.is_privmsg:
        user_key = HabIRC.api_regex.findall(args[2])

        if len(user_key) > 0:
            user_key = user_key[0]
        else:
            bot.reply(trigger.nick, "Invalid API Token")
            return

        bot.db.set_nick_value(trigger.nick, 'habitica_api_key', user_key)
        bot.msg(trigger.nick, "Saved your API Token.")
    else:
        bot.reply("You just posted your Habitica password in a public channel. "
                  + color(bold("Go change it RIGHT NOW!"), "red"))


def info_key(bot, trigger):
    if trigger.is_privmsg:
        bot.msg(trigger.nick, "Please note that the API Token can be used as a " + color("password", "red")
                + " and you should never give it to anyone you don't trust!")
        bot.msg(trigger.nick, "Be aware that BAD THINGS can happen, and your API Token might be made public.")
        bot.msg(trigger.nick, "IN NO EVENT SHALL THE OPERATORS OF THIS BOT BE LIABLE FOR ANY CLAIM, DAMAGES OR " +
                "OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN" +
                "CONNECTION WITH THE BOT OR THE USE OR OTHER DEALINGS IN THE BOT.")
        bot.msg(trigger.nick, "" + color(bold("YOU HAVE BEEN WARNED!"), "red"))
        bot.msg(trigger.nick, "If you ARE SURE want this bot to save your API Token, add it with " +
                "'.status key DANGER <API Token>'")

    else:
        bot.reply("Please do not configure me in a public channel!")


def info_user(bot, trigger):
    if trigger.is_privmsg:
        bot.msg(trigger.nick, "Please give me your Habitica User ID with '.status user <User ID>'")
    else:
        bot.reply("Please do not configure me in a public channel!")


def del_user(bot, trigger):
    if bot.db.get_nick_value(trigger.nick, "habitica_api_user") is not None:
        bot.db.delete_nick_group(trigger.nick)
        bot.reply("Deleted all your settings.")
    else:
        bot.reply("I do not know you, sorry.")


def start_configuration(bot, trigger):
    if not trigger.is_privmsg:
        bot.reply("Opening query for configuration.")
    bot.msg(trigger.nick, "Please give me your Habitica User ID with '.status user <User ID>'.")


@sopel.module.interval(60)
def read_chat(bot):
    chat = requests.get("https://habitica.com/api/v2/groups/habitrpg/chat", headers=HabIRC.auth)

    if chat.status_code != 200:
        return

    for channel in bot.config.habirc.channels:

        if channel in bot.channels:

            for line in xrange(30, -1, -1):

                timestamp = int(chat.json()[line]["timestamp"])

                if timestamp <= HabIRC.last_timestamp[channel]:
                    continue

                uuid = chat.json()[line]["uuid"]

                if uuid == "system":
                    bot.msg(channel, color(chat.json()[line]["text"][1:-1], "pink"))
                else:
                    user = requests.get("https://habitica.com/api/v2/members/" + uuid, headers=HabIRC.auth)

                    name = " " + user.json()["profile"]["name"] + " "
                    colors = get_name_colors(user.json())
                    message = chat.json()[line]["text"]
                    bot.msg(channel, color(name, colors[0], colors[1]) + " " + message)

            HabIRC.last_timestamp[channel] = int(chat.json()[0]["timestamp"])
            bot.db.set_channel_value(channel, "last_timestamp", HabIRC.last_timestamp[channel])
