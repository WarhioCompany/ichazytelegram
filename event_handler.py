from datetime import datetime

from db_data.models import Event
from db_data.db_session import session_scope
from enum import Enum

from sqlalchemy import and_


class EventType(Enum):
    user_subscribed = 1
    user_registered = 2
    user_was_invited = 3


def add_event(user_id, event_type, date=None):
    if not date:
        date = datetime.now().timestamp()
    with session_scope() as session:
        event = Event(
            user_id=user_id,
            event_type=event_type.name,
            date=date,
            active=True
        )
        session.add(event)
        session.commit()


def get_user_events(user_id, event_type):
    with session_scope() as session:
        data = session.query(Event).filter(
            and_(Event.user_id == user_id, Event.event_type == event_type.name, Event.active)).all()
        return data


def get_active_events(event_type):
    with session_scope() as session:
        data = session.query(Event).filter(and_(Event.event_type == event_type.name, Event.active)).all()
        return data


def get_event(user_id, event_type):
    events = get_user_events(user_id, event_type)
    if events:
        return events[-1]
    else:
        return None


def remove_event(user_id, event_type):
    with session_scope() as session:
        session.query(Event).filter(and_(Event.user_id == user_id, Event.event_type == event_type.name)).delete()
        session.commit()


def set_event_activity(user_id, event_type, active):
    with session_scope() as session:
        events = session.query(Event).filter(and_(Event.user_id == user_id, Event.event_type == event_type.name)).all()
        if events:
            events[-1].active = active


# time measures in seconds
def minute():
    return 60


def hour():
    return minute() * 60


def day():
    return hour() * 24


def week():
    return day() * 7
