from uqcsbot import bot, Command


@bot.on_command("cat")
def handle_cat(command: Command):
    cat = "```\n" + \
          "         __..--''``\\--....___   _..,_\n" + \
          "     _.-'    .-/\";  `        ``<._  ``-+'~=.\n" + \
          " _.-' _..--.'_    \\                    `(^) )\n" + \
          "((..-'    (< _     ;_..__               ; `'   fL\n" + \
          "           `-._,_)'      ``--...____..-'\n```"

    bot.post_message(command.channel, cat)
