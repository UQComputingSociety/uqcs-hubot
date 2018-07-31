"""
Tests for yt.py
"""
from test.conftest import MockUQCSBot, TEST_CHANNEL_ID
from unittest.mock import patch

YOUTUBE_VIDEO_URL = 'https://www.youtube.com/watch?v='
# TODO(mitch): work out a way to get this from yt.py without triggering
# 'on_command' to be called and add '!yt' as a handler which messes with
# testing.
NO_QUERY_MESSAGE = "You can't look for nothing. !yt <QUERY>"


def mocked_search_execute(search_query: str, search_part: str, search_type: str, max_results: int):
    """
    Currently only returns a response of video ID's based on max_results.
    Otherwise returns none.
    """
    if search_type == 'video' and search_part == 'id':
        items = [{'id': {'videoId': str(i).zfill(11)}} for i in range(max_results)]
        return {'items': items}
    return None


def test_yt_no_query(uqcsbot: MockUQCSBot):
    """
    This test aims to test the stability of the script when no query is given.
    """
    uqcsbot.post_message(TEST_CHANNEL_ID, "!yt")
    messages = uqcsbot.test_messages.get(TEST_CHANNEL_ID, [])
    assert len(messages) == 2
    assert messages[-1]['text'] == NO_QUERY_MESSAGE


@patch('uqcsbot.scripts.yt.execute_search', new=mocked_search_execute)
def test_yt_normal(uqcsbot: MockUQCSBot):
    """
    This test aims to test the basic functionality of the yt script.
    The mocked function replaces the googleapiclient functionality.
    """
    uqcsbot.post_message(TEST_CHANNEL_ID, "!yt dog")
    messages = uqcsbot.test_messages.get(TEST_CHANNEL_ID, [])
    assert len(messages) == 2
    assert messages[-1]['text'][0:len(YOUTUBE_VIDEO_URL)] == YOUTUBE_VIDEO_URL
