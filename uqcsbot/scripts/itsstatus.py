from uqcsbot import bot, Command
from requests import get
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from uqcsbot.utils.command_utils import loading_status

ITS_SERVICE_UPDATES_URL = "https://my.uq.edu.au/information-and-services" + \
    "/information-technology/it-service-updates"


ERROR_MESSAGE = "I tried to get service updates but I failed. Error with HTTP Request."


@bot.on_command("itsstatus")
@loading_status
def handle_itsstatus(command: Command):
    service_updates = get_its_service_updates()

    if service_updates is None:
        bot.post_message(command.channel_id, ERROR_MESSAGE)
        return

    message = "```"

    for update in service_updates:
        if update["status"] == "Resolved":
            continue

        message += f"Title: {update['title']}\n"
        message += f"{update['details']}\n"
        message += f"---\n"

    message += "```"

    bot.post_message(command.channel_id, message)


def get_its_service_updates():
    updates_html = get_updates_page()

    if updates_html is None:
        return None

    return get_updates_from_page(updates_html)


def get_updates_from_page(updates_page):
    """
    Get a list of all updates from updates page
    """
    html = BeautifulSoup(updates_page, "html.parser")

    update_items = []

    for div in html.select(".service-view__event"):
        title = div.select(".service-view__event-title")[0].get_text()
        status = div.select(".service-view__event-availability")[0].get_text()
        details = div.select(".service-view__event-details")[0].get_text()
        start_date = div.select(
            ".service-view__event-start-date")[0].get_text()
        end_date = div.select(".service-view__event-end-date")[0].get_text()

        update_items.append(
            {"title": title,
             "status": status,
             "details": details,
             "start_date": start_date,
             "end_date": end_date})

    return update_items


def get_updates_page():
    """
    Gets the service updates page HTML
    """
    headers = {'User-Agent': 'UQCS'}
    try:
        resp = get(ITS_SERVICE_UPDATES_URL, headers=headers)
        return resp.content
    except RequestException as e:
        bot.logger.error(
            f"A request error occurred:\n{e.content}")
        return None
