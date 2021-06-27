from test.conftest import MockUQCSBot, TEST_CHANNEL_ID
from unittest.mock import patch

GOOD_MESSAGE = ("```Title: Routine server maintenence for Jac Production.\n"
                + "GITF (Global IT Factory is the Vendor) / Jac will be conducting routine server"
                + " maintenance and this requires downtime.\n"
                + "Reason: Hardening production services based on Oracle recommendations to apply"
                + " updated privileges to system accounts for Oracle cloud object storage.  GITF"
                + " have tested the change and implemented the configuration on other client"
                + " systems with no issues.\n"
                + "\n"
                + "This change will be performed across all instances: Pre-test, Test and"
                + " production\n"
                + "\n"
                + "---\n"
                + "Title: Emergency restart required.\n"
                + "The Learn.UQ service will be restarted to resolve an issue with exam"
                + " availability.\n"
                + "\n"
                + "Central exams are finished for the day before 8pm, , however students are"
                + " advised against attempting 24 hour window exams during this time.\n"
                + "---\n"
                + "Title: Isilon 01 intermittent sync issue to secondary site\n"
                + "An issue has been identified that is intermittently affecting the sync of"
                + " data to the secondary site.\n"
                + "\n"
                + "There is no data availability issue, however DR capability is reduced.  \n"
                + "\n"
                + "ITS are working with the vendor to resolve the issue.\n"
                + "---\n"
                + "Title: UQ Book It user group synching\n"
                + "UQ Book It access synched from AD is currently non-functional. Existing"
                + " members of these groups and access provided in other manners is still"
                + " functional.\n"
                + "---\n"
                + "```")


def mocked_html_get(*args, **kwargs):
    """
    This method will be used to replace the requests response
    Returns locally stored HTML that represents a typically scraped response.
    """
    f = open("test/IT_service_updates.html", "r")
    return f.read()


@patch("uqcsbot.scripts.itsstatus.get_updates_page", new=mocked_html_get)
def test_itsstatus_normal(uqcsbot: MockUQCSBot):
    """
    This test aims to determine that a typical HTML response will result in a typical message.
    By mocking the get_search_page function with mocked_html_get
    no online functionality is required.
    """
    uqcsbot.post_message(TEST_CHANNEL_ID, "!itsstatus")
    messages = uqcsbot.test_messages.get(TEST_CHANNEL_ID, [])
    assert len(messages) == 2
    assert messages[1].get('text') == GOOD_MESSAGE
