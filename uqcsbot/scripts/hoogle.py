from uqcsbot import bot, Command
import requests
import json
import html
import argparse
from uqcsbot.utils.command_utils import loading_status, UsageSyntaxException


# Base hoogle API url with preset mode, start and count parameters.
BASE_URL = "https://www.haskell.org/hoogle/?mode=json&count=10&hoogle="


def pretty_hoogle_result(result: dict, is_verbose: bool) -> str:
    url = result['location']
    type_sig = result['self']
    docs = result['docs']

    if is_verbose:
        return f"`{type_sig}` <{url}|link>\n{docs}"
    else:
        return f"`{type_sig}` <{url}|link>"


@bot.on_command("hoogle")
@loading_status
def handle_hoogle(command: Command):
    '''
    `!hoogle [-v] [--verbose] <TYPE_SIGNATURE>` - Queries the Hoogle Haskell API search engine,
    searching Haskell libraries by either function name, or by approximate type signature.
    '''
    command_args = command.arg.split() if command.has_arg() else []

    arg_parser = argparse.ArgumentParser()
    def usage_error(*args, **kwargs):
        raise UsageSyntaxException()
    arg_parser.error = usage_error  # type: ignore
    arg_parser.add_argument('-v', '--verbose', action='store_true')
    arg_parser.add_argument('type_signature')

    parsed_args = arg_parser.parse_args(command_args)
    http_response = requests.get(BASE_URL + html.unescape(parsed_args.type_signature))
    if http_response.status_code != requests.codes.ok:
        bot.post_message(command.channel_id, "Problem fetching data")
        return

    results = json.loads(http_response.content).get('results', [])
    if len(results) == 0:
        bot.post_message(command.channel_id, "No results found")
        return

    message = "\n".join(pretty_hoogle_result(result, parsed_args.verbose) for result in results)
    bot.post_message(command.channel_id, message)
