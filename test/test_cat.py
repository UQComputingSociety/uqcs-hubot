from test.conftest import MockUQCSBot, TEST_CHANNEL_ID
from test.helpers import generate_message_object

# TODO(mitch): work out a way to get the cat from cat.py without triggering
# 'on_command' to be called and add '!cat' as a handler which messes with
# testing.

def test_cat(uqcsbot: MockUQCSBot):
    '''
    test !cat
    '''
    message = generate_message_object(TEST_CHANNEL_ID, '!cat')
    uqcsbot.post_and_handle_message(message)
    channel = uqcsbot.test_channels.get(TEST_CHANNEL_ID)
    assert channel is not None
    assert len(channel.get('messages', [])) == 2
