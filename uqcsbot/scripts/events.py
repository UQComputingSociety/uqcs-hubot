import re
import requests

from typing import List
from datetime import date, datetime, timedelta
from calendar import month_name, month_abbr, day_abbr
from icalendar import Calendar
from slackblocks import Attachment, SectionBlock
from pytz import timezone, utc
from typing import Tuple, Optional
from dateutil.rrule import rrulestr

from uqcsbot import bot, Command
from uqcsbot.utils.command_utils import UsageSyntaxException, loading_status
from uqcsbot.utils.itee_seminar_utils import (get_seminars, HttpException, InvalidFormatException)

UQCS_CALENDAR_URL = "https://calendar.google.com/calendar/ical/" \
                    "q3n3pce86072n9knt3pt65fhio%40group.calendar.google.com/public/basic.ics"
EXTERNAL_CALENDAR_URL = "https://calendar.google.com/calendar/ical/" \
                        "72abf01afvsl3bjd9oq2g1avgg%40group.calendar.google.com/public/basic.ics"
FILTER_REGEX = re.compile('full|all|[0-9]+( weeks?)?|jan.*|feb.*|mar.*'
                          + '|apr.*|may.*|jun.*|jul.*|aug.*|sep.*|oct.*|nov.*|dec.*')
BRISBANE_TZ = timezone('Australia/Brisbane')
MONTH_NUMBER = {month.lower(): index for index, month in enumerate(month_abbr)}

MAX_RECURRING_EVENTS = 3


class EventFilter(object):
    def __init__(self, full=False, weeks=None, cap=None, month=None, is_valid=True):
        self.is_valid = is_valid
        self._full = full
        self._weeks = weeks
        self._cap = cap
        self._month = month

    @classmethod
    def from_argument(cls, argument: str):
        if not argument:
            return cls(weeks=2)
        else:
            match = re.match(FILTER_REGEX, argument.lower())
            if not match:
                return cls(is_valid=False)
            filter_str = match.group(0)
            if filter_str in ['full', 'all']:
                return cls(full=True)
            elif 'week' in filter_str:
                return cls(weeks=int(filter_str.split()[0]))
            elif filter_str[:3] in MONTH_NUMBER:
                return cls(month=MONTH_NUMBER[filter_str[:3]])
            else:
                return cls(cap=int(filter_str))

    def filter_events(self, events: List['Event'], start_time: datetime):
        if self._weeks is not None:
            end_time = start_time + timedelta(weeks=self._weeks)
            return [e for e in events if e.start < end_time]
        if self._month is not None:
            return [e for e in events if e.start.month == self._month]
        elif self._cap is not None:
            return events[:self._cap]
        return events

    def get_header(self):
        if self._full:
            return "List of *all* upcoming events:"
        elif self._weeks is not None:
            return f"Events in the next *{self._weeks} weeks*:"
        elif self._month is not None:
            return f"Events in *{month_name[self._month]}*:"
        else:
            return f"The *next {self._cap} events*:"

    def get_no_result_msg(self):
        if self._weeks is not None:
            return f"There don't appear to be any events in the next *{self._weeks}* weeks"
        elif self._month is not None:
            return f"There don't appear to be any events in *{month_name[self._month]}*"
        else:
            return "There don't appear to be any upcoming events..."


class Event(object):
    def __init__(self, start: datetime, end: datetime,
                 location: str, summary: str, recurring: bool,
                 link: Optional[str], source: Optional[str] = None):
        self.start = start
        self.end = end
        self.location = location
        self.summary = summary
        self.recurring = recurring
        self.link = link
        self.source = source

    @classmethod
    def encode_text(cls, text: str) -> str:
        """
        Encodes user-specified text so that it is not interpreted as command characters
        by Slack. Implementation as required by: https://api.slack.com/docs/message-formatting
        Note that this encoding process does not stop injection of text effects (bolding,
        underlining, etc.), or a malicious user breaking the text formatting in the events
        command. It should, however, prevent <, & and > being misinterpreted and including
        links where they should not.
        --
        :param text: The text to encode
        :return: The encoded text
        """
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    @classmethod
    def from_cal_event(cls, cal_event, source: str = "UQCS", recurrence_dt: datetime = None):
        """
        Converts an ical event to an Event

        :param cal_event: event to convert
        :param source: the calendar the event was sourced from
        :param recurrence_dt: if this is a one off event then None
                                else the date of this instance of a recurring event
        """
        if recurrence_dt:
            start = recurrence_dt
            end = recurrence_dt + (cal_event.get('DTEND').dt - cal_event.get('DTSTART').dt)

        else:
            start = cal_event.get('dtstart').dt
            end = cal_event.get('dtend').dt
            # ical 'dt' properties are parsed as a 'DDD' (datetime, date, duration) type.
            # The below code converts a date to a datetime, where time is set to midnight.
            if isinstance(start, date) and not isinstance(start, datetime):
                start = datetime.combine(start, datetime.min.time()).astimezone(utc)
            if isinstance(end, date) and not isinstance(end, datetime):
                end = datetime.combine(end, datetime.max.time()).astimezone(utc)
        location = cal_event.get('location', 'TBA')
        summary = cal_event.get('summary')
        return cls(start, end, location,
                   f"{'[External] ' if source == 'external' else ''}{summary}",
                   recurrence_dt is not None, None, source)

    @classmethod
    def from_seminar(cls, seminar_event: Tuple[str, str, datetime, str]):
        title, link, start, location = seminar_event
        # ITEE doesn't specify the length of seminars, but they are normally one hour
        end = start + timedelta(hours=1)
        # Note: this
        return cls(start, end, location, f"[ITEE Seminar] {title}", False, link, "ITEE")

    def __str__(self):
        d1 = self.start.astimezone(BRISBANE_TZ)
        d2 = self.end.astimezone(BRISBANE_TZ)

        start_str = (f"{day_abbr[d1.weekday()].upper()}"
                     + f" {month_abbr[d1.month].upper()} {d1.day} {d1.hour}:{d1.minute:02}")
        if (d1.month, d1.day) != (d2.month, d2.day):
            end_str = (f"{day_abbr[d2.weekday()].upper()}"
                       + f" {month_abbr[d2.month].upper()} {d2.day} {d2.hour}:{d2.minute:02}")
        else:
            end_str = f"{d2.hour}:{d2.minute:02}"

        # Encode user-provided text to prevent certain characters
        # being interpreted as slack commands.
        summary_str = Event.encode_text(("[Recurring] " if self.recurring else "") + self.summary)
        location_str = Event.encode_text(self.location)

        if self.link is None:
            return f"{'*' if self.source == 'UQCS' else ''}" \
                   f"`{summary_str}`" \
                   f"{'*' if self.source == 'UQCS' else ''}\n" \
                   f"*{start_str} - {end_str}* {'_(' + location_str + ')_' if location_str else ''}"
        else:
            return f"`<{self.link}|{summary_str}>`\n" \
                   f"*{start_str} - {end_str}* {'_(' + location_str + ')_' if location_str else ''}"


def get_current_time():
    """
    Returns the current date and time
    This function exists purely so it can be mocked for testing
    """
    return datetime.now(tz=BRISBANE_TZ).astimezone(utc)


def handle_calendar(calendar) -> List[Event]:
    """
    Returns a list of events from a calendar
    """
    events = []
    current_time = get_current_time()
    # subcomponents are how icalendar returns the list of things in the calendar
    for component in calendar.subcomponents:
        # we are only interested in ones with the name VEVENT as they
        # are events
        if component.name != 'VEVENT':
            continue
        elif component.get('RRULE') is not None:
            # If the until date exists, update it to UTC
            if component['RRULE'].get('UNTIL') is not None:
                until = datetime.combine(component['RRULE']['UNTIL'][0], datetime.min.time()) \
                            .astimezone(utc)
                component['RRULE']['UNTIL'] = [until]
            rule = rrulestr('\n'.join([
                    line for line in component.content_lines()
                    if line.startswith('RRULE')
                    or line.startswith('EXDATE')
                ]), dtstart=component.get('DTSTART').dt)
            rule = [dt for dt in list(rule) if dt > current_time]
            for dt in rule[:MAX_RECURRING_EVENTS]:
                dt = dt.replace(tzinfo=BRISBANE_TZ)
                event = Event.from_cal_event(component, recurrence_dt=dt)
                events.append(event)
        else:
            # we convert it to our own event class
            event = Event.from_cal_event(component)
            # then we want to filter out any events that are not after the current time
            if event.start > current_time:
                events.append(event)

    return events

@bot.on_command('events')
@loading_status
def handle_events(command: Command):
    """
    `!events [full|all|NUM EVENTS|<NUM WEEKS> weeks] [uqcs|itee]`
    - Lists all the UQCS and/or  ITEE events that are
    scheduled to occur within the given filter.
    If unspecified, will return the next 2 weeks of events.
    """

    argument = command.arg if command.has_arg() else ""
    current_time = get_current_time()

    source_get = {"uqcs": False, "itee": False, "external": False}
    for k in source_get:
        if k in argument:
            source_get[k] = True
            argument = argument.replace(k, "")
    argument = argument.strip()
    if not any(source_get.values()):
        source_get = dict.fromkeys(source_get, True)

    event_filter = EventFilter.from_argument(argument)
    if not event_filter.is_valid:
        raise UsageSyntaxException()

    events = []

    if source_get["uqcs"]:
        uqcs_calendar = Calendar.from_ical(get_calendar_file("uqcs"))
        events += handle_calendar(uqcs_calendar)
    if source_get["external"]:
        external_calendar = Calendar.from_ical(get_calendar_file("external"))
        events += handle_calendar(external_calendar)
    if source_get["itee"]:
        try:
            # Try to include events from the ITEE seminars page
            seminars = get_seminars()
            for seminar in seminars:
                # The ITEE website only lists current events.
                event = Event.from_seminar(seminar)
                events.append(event)
        except (HttpException, InvalidFormatException) as e:
            bot.logger.error(e.message)

    # then we apply our event filter as generated earlier
    events = event_filter.filter_events(events, current_time)
    # then, we sort the events by date
    events = sorted(events, key=lambda event_: event_.start)

    attachments = []
    if not events:
        message_text = f"_{event_filter.get_no_result_msg()}_\n" \
                       f"For a full list of events, visit: " \
                       f"https://uqcs.org/events " \
                       f"and https://www.itee.uq.edu.au/seminar-list"
    else:
        for event in events:
            color = "#5297D1" if event.source == "UQCS" else \
                "#51237A" if event.source == "ITEE" else "#116B17"
            attachments.append(Attachment(SectionBlock(str(event)), color=color))
        message_text = f"_{event_filter.get_header()}_"

    bot.post_message(command.channel_id, text=message_text,
                     attachments=[attachment._resolve() for attachment in attachments])


def get_calendar_file(calendar: str = "uqcs") -> bytes:
    """
    Loads the UQCS or External Events calender .ics file from Google Calendar.
    This method is mocked by unit tests.
    :return: The returned ics calendar file, as a stream
    """
    if calendar == "uqcs":
        http_response = requests.get(UQCS_CALENDAR_URL)
    else:
        http_response = requests.get(EXTERNAL_CALENDAR_URL)
    return http_response.content
