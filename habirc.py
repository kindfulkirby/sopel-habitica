import sopel.module
import requests
from sopel.config.types import StaticSection, ValidatedAttribute, ListAttribute
from sopel.formatting import color, bold, underline
import re


class HabIRC():
    auth = {}
    last_timestamp = 0
    api_regex = re.compile(ur'[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}')


class HabircSection(StaticSection):
    wait_time = ValidatedAttribute('wait_time', int, default=60)
    api_user = ValidatedAttribute('api_user')
    api_key = ValidatedAttribute('api_key')
    channels = ListAttribute('channels')


def setup(bot):
    bot.config.define_section('habirc', HabircSection)
    HabIRC.auth = {"x-api-key": bot.config.habirc.api_key, "x-api-user": bot.config.habirc.api_user}


@sopel.module.commands('status')
def status(bot, trigger):
    """Replies with the configured character's status (HP, MP, XP & Gold)"""

    if trigger.group(3) == "add":
        if not trigger.is_privmsg:
            bot.reply("Opening query for configuration")
        bot.msg(trigger.nick, "Please give me your Habitica User ID with '.status user <User ID>'")

    elif trigger.group(3) == "del":
        if bot.db.get_nick_value(trigger.nick, "habitica_api_user") is not None:
            bot.db.delete_nick_group(trigger.nick)
            bot.reply("Deleted all your settings.")
        else:
            bot.reply("I do not know you, sorry.")

    elif trigger.group(3) == "user" and trigger.group(4) is not None:
        if trigger.is_privmsg:
            user_id = HabIRC.api_regex.findall(trigger.group(4))

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
            bot.msg(trigger.nick, " ")
            bot.msg(trigger.nick, "If you want more details or use me to cast spells or use potions, you can " +
                    " optionally add your API Token.")
            bot.msg(trigger.nick, "If you want this bot to save your API Token, add it with '.status key'")

        else:
            bot.reply("Please do not configure me in a public channel!")

    elif trigger.group(3) == "user" and trigger.group(4) is None:
        if trigger.is_privmsg:
            bot.msg(trigger.nick, "Please give me your Habitica User ID with '.status user <User ID>'")
        else:
            bot.reply("Please do not configure me in a public channel!")

    elif trigger.group(3) == "key" and trigger.group(4) is not "DANGER":
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

    elif trigger.group(3) == "key" and trigger.group(4) == "DANGER" and trigger.group(5) is not None:
        if trigger.is_privmsg:
            user_key = HabIRC.api_regex.findall(trigger.group(5))

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

    elif trigger.group(3) is None:
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
            raise requests.ConnectionError

        hp = str(round(user.json()["stats"]["hp"], 2))
        mp = str(int(user.json()["stats"]["mp"]))
        gp = str(round(user.json()["stats"]["gp"], 2))
        xp = str(int(user.json()["stats"]["exp"]))
        name = user.json()["profile"]["name"]

        if api_key is not None:
            max_hp = user.json()["stats"]["maxHealth"]
            max_mp = user.json()["stats"]["maxMP"]
            to_next_level = user.json()["stats"]["toNextLevel"]

            hp = hp + "/" + str(max_hp)
            mp = mp + "/" + str(max_mp)
            xp = xp + "/" + str(to_next_level)

        sep = " | "

        bot.reply(color(" " + name + " ", "white", "grey") + " " + color(hp + " HP", "red") + sep + color(mp + " MP", "blue")
                  + sep + color(xp + " XP", "yellow") + sep + color(gp + " Gold", "olive"))

    else:
        bot.reply("Unknown command")

@sopel.module.interval(60)
def read_chat(bot):
    chat = requests.get("https://habitica.com/api/v2/groups/party/chat", headers=HabIRC.auth)

    if chat.status_code != 200:
        raise requests.ConnectionError

    for channel in bot.config.habirc.channels:

        if channel in bot.channels:

            for line in xrange(30, -1, -1):

                timestamp = int(chat.json()[line]["timestamp"])

                if timestamp <= HabIRC.last_timestamp:
                    continue

                uuid = chat.json()[line]["uuid"]

                if uuid == "system":
                    bot.msg(channel, color(chat.json()[line]["text"][1:-1], "pink"))
                else:
                    user = color(" " + chat.json()[line]["user"] + " ", "white", "grey")
                    bot.msg(channel, user + chat.json()[line]["text"])

            HabIRC.last_timestamp = int(chat.json()[0]["timestamp"])