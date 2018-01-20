from slackclient import SlackClient
from typing import List


# see https://api.slack.com/docs/pagination for details
def paginate_api_call(client: SlackClient, method: str, *args, **kwargs):
    responses = []
    while kwargs.get("cursor") != "":
        response = client.api_call(method, *args, **kwargs)
        responses.append(response)
        kwargs["cursor"] = response["response_metadata"]["next_cursor"]
    return responses


class Channel(object):
    def __init__(self, client: SlackClient, channel_name: str):
        self.name = channel_name
        self.client = client

    def get_members(self) -> List[str]:
        member_pages = paginate_api_call(self.client, "conversations.members", channel=self.name)
        members = []
        for page in member_pages:
            members += page["members"]
        return members


class Bot(object):
    def __init__(self, client: SlackClient):
        self.client = client

    def post_message(self, channel: Channel, text: str):
        self.client.api_call("chat.postMessage", channel=channel.name, text=text)