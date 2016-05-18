# Sopel Habitica Module
[Sopel][1] IRC bot module for [Habitica][2]

The chosen unicode icons look best with [good emoji support][3].

## Features 

Working so far:

* Echoes Habitica party chat into IRC
* Talk in chat from IRC
* .hero command displays character status
* Shows nick colors
* Disable colors (not recommended)
* Renders markdown code blocks in colors (if enabled)

Planned Features:

* Cast spells from IRC
* Use Health potion from IRC
* Autoheal

Maybe Features:

* Add Habits/Dailies/Todos
* Up/Down/Complete Habits/Dailies/Todos/Checklists

## Installation

Clone this repository, open a terminal in the directory you cloned it to and run `pip install .`.  
Soon to be found in pypi, too!

## Configuration

Edit your Sopel config file (normally `.sopel/default.cfg`).

Under `[core]` add `habitica` to `enable=` to enable the module.

Then put in this section

```
[habitica]  
api_user = <a Habitica User ID>
api_key = <the corresponding API Token>
channels = <comma separated list of IRC channels you want a Habitica chat in>
chats = <comma separated list of Habitca chat IDs (see below)>
```

Those are the *mandatory* configuration lines.  
`chats=` can contain either the UUID of a chat, or `party` for your current party's chat or `habitrpg` for the Tavern
chat.

### Optional configuration  

The following lines optionally go in the `[habitica]` section, the values behind them are the default values:

``` 
max_lines = 5
colors = True
api_url = https://habitica.com/api/v2/
```

`max_lines` is the number of lines (each of which is limited to 400 characters) each IRC message can be long.  
`colors` can be set to `False` to deactivate the colors for this module. Makes it much harder to read, though!
`api_url` is the url of the Habitica API. If you have your own version of Habitica running, you might want to change it.

## TODO

* Tests
* Documentation


[1]: https://github.com/sopel-irc/sopel
[2]: https://habitica.com
[3]: https://github.com/eosrei/emojione-color-font
