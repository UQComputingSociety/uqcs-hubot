from uqcsbot import bot, Command
from urllib.parse import quote
import re


def handle_latex_internal(channel, data):
    url = f"http://latex.codecogs.com/gif.latex?{quote(data)}"
    bot.post_message(
        channel,
        text=f"LaTeX render for \"{data}\"",
        attachments=[
            {
                "fallback": f"Codecogs LaTeX image for {data}",
                "image_url": url,
                "footer": "From latex.codecogs.com"
            }
        ],
        unfurl_links=False,
        unfurl_media=False,
    )


@bot.on_command("latex")
def handle_latex_cmd(command: Command):
    """
    `!latex CONTENT` - Renders `CONTENT` to LaTeX and sends it to Slack.
    `$$ CONTENT $$` also works.
    """
    if not command.has_arg():
        bot.post_message(command.channel_id, "No data provided")
    handle_latex_internal(command.channel_id, command.arg.strip())


@bot.on('message')
def handle_latex_evt(evt):
    if 'subtype' in evt:
        # Only handle evt on raw messages from users
        return
    match = re.search(r"\$\$(.+)\$\$", evt['text'])
    if match is None:
        return
    handle_latex_internal(evt['channel'], match.group(1).strip())
