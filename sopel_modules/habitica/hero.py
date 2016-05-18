# -*- coding: utf8 -*-

from __future__ import absolute_import

import requests
from sopel.formatting import color, bold

from .common import Common, get_name_colors


def user_add(bot, trigger):
    argument = trigger.group(4)

    if argument is not None:
        user_configure(argument, bot, trigger)
    else:
        start_configuration(bot, trigger)


def user_configure(argument, bot, trigger):
    if trigger.is_privmsg:
        user_ids = Common.uuid_regex.findall(argument)

        if len(user_ids) > 0:
            user_id = user_ids[0]
        else:
            bot.msg(trigger.nick, "Invalid user ID")
            return

        bot.db.set_nick_value(trigger.nick, 'habitica_api_user', user_id)

        user = requests.get(bot.config.habitica.api_url + "members/" + user_id, headers=Common.auth)
        name = user.json()["profile"]["name"]

        bot.msg(trigger.nick, "Saved your character " + name)
        bot.msg(trigger.nick, "If you ever want to delete your settings, use '.hero del'")
        bot.msg(trigger.nick, "If you want more details or use me to cast spells, use potions or talk in the chat, " +
                "you can optionally add your API Token.")
        bot.msg(trigger.nick, "If you want this bot to save your API Token, add it with '.hero key'")

    else:
        bot.reply("Please do not configure me in a public channel!")


def start_configuration(bot, trigger):
    if not trigger.is_privmsg:
        bot.reply("Opening query for configuration.")
    bot.msg(trigger.nick, "Please give me your Habitica User ID with '.hero add <User ID>'.")


def user_del(bot, trigger):
    if bot.db.get_nick_value(trigger.nick, "habitica_api_user") is not None:
        bot.db.delete_nick_group(trigger.nick)
        bot.reply("Deleted all your settings.")
    else:
        bot.reply("I do not know you, sorry.")


def key_add(bot, trigger):
    arguments = [trigger.group(4), trigger.group(5)]

    if arguments[0] == "IHAVEBEENWARNED" and arguments[1] is not None:
        key_configure(arguments[1], bot, trigger)
    else:
        key_info(bot, trigger)


def key_configure(argument, bot, trigger):
    if trigger.is_privmsg:
        user_keys = Common.uuid_regex.findall(argument)

        if len(user_keys) > 0:
            user_key = user_keys[0]
        else:
            bot.reply(trigger.nick, "Invalid API Token")
            return

        bot.db.set_nick_value(trigger.nick, 'habitica_api_key', user_key)
        bot.msg(trigger.nick, "Saved your API Token.")

    else:
        bot.reply("You just posted your Habitica password in a public channel. "
                  + color(bold("Go change it RIGHT NOW!"), "red"))


def key_info(bot, trigger):
    if not trigger.is_privmsg:
        bot.reply("Opening query for configuration.")

    bot.msg(trigger.nick, "Please note that the API Token can be used as a " + color("password", "red")
            + " and you should never give it to anyone you don't trust!")
    bot.msg(trigger.nick, "Be aware that BAD THINGS can happen, and your API Token might be made public.")
    bot.msg(trigger.nick, "IN NO EVENT SHALL THE OPERATORS OF THIS BOT BE LIABLE FOR ANY CLAIM, DAMAGES OR " +
            "OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN" +
            "CONNECTION WITH THE BOT OR THE USE OR OTHER DEALINGS IN THE BOT.")
    bot.msg(trigger.nick, "" + color(bold("YOU HAVE BEEN WARNED!"), "red"))
    bot.msg(trigger.nick, "If you ARE SURE want this bot to save your API Token, add it with " +
            "'.hero key IHAVEBEENWARNED <API Token>'")


def show_status(bot, trigger):
    api_user = bot.db.get_nick_value(trigger.nick, 'habitica_api_user')
    api_key = bot.db.get_nick_value(trigger.nick, 'habitica_api_key')

    if api_user is None:
        bot.reply("I do not know you, sorry. Please use '.hero add'.")
        return

    else:
        if api_key is None:
            user = requests.get(bot.config.habitica.api_url + "members/" + api_user, headers=Common.auth)
        else:
            headers = {"x-api-key": api_key, "x-api-user": api_user}
            user = requests.get(bot.config.habitica.api_url + "user", headers=headers)

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

    seperator = " | "

    bot.say("Status for "
            + color(Common.name_prefix + name + Common.name_suffix, name_colors[0], name_colors[1]) + " "
            + color(bold(u"♥ ") + hp + " HP", Common.hp_color) + seperator
            + color(bold(u"⚡ ") + mp + " MP", Common.mp_color) + seperator
            + color(bold(u"⭐ ") + xp + " XP", Common.xp_color) + seperator
            + color(bold(u"⛁ ") + gp + " Gold", Common.gp_color)
            )


commands = {
    "add": user_add,
    "del": user_del,
    "key": key_add,
    None: show_status
}


def hero_command(bot, trigger):
    """Replies with the configured character's status (HP, MP, XP & Gold)"""

    command = trigger.group(3)

    if command in commands:
        # noinspection PyCallingNonCallable
        commands[command](bot, trigger)
    else:
        bot.reply("Unknown command")
