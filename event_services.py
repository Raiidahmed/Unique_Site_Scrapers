from datetime import datetime

from scraper import db
from scraper.constants.cities import CITIES, CitySlugs
from scraper.models import Event, EventConstants
from scraper.services.gpt_services import gpt_summarize_event
from sqlalchemy.exc import IntegrityError


def future_events(events) -> list[Event]:
    return [e for e in events if e.start_datetime() >= datetime.now().astimezone()]

def get_all_events():
    return Event.query.all()

def get_events_by_city(city_slug):
    return Event.query.filter_by(city_slug=city_slug).all() 

def get_approved_events(city_tag=None):
    if city_tag:
        return Event.query.filter_by(status='approved', city_tag=city_tag).all()
    else:
        return Event.query.filter_by(status='approved').all()

def sort_events_by_date(events):
    return sorted(events, key=lambda e: e.start_date)

def update_event_emojis():
    events = Event.query.filter_by(emoji=None).all()
    for event in events:
        event.generate_emoji()
        db.session.add(event)
        db.session.commit()

def update_event_status(event_id, new_status):
    event = Event.query.get(event_id)
    if event:
        event.status = new_status
        db.session.add(event)
        db.session.commit()
        return 'Status updated successfully'
    else:
        return 'Event not found'

def approve_event(event_id):
    event = Event.query.get(event_id)
    print("Approving event")
    if event:
        print("Event found")
        event.status = EventConstants.APPROVED.value
        db.session.add(event)
        db.session.commit()
        return True 
    else:
        return False

def reject_event(event_id):
    event = Event.query.get(event_id)
    if event:
        event.status = EventConstants.REJECTED.value
        db.session.add(event)
        db.session.commit()
        return True 
    else:
        return False

def save_event_from_jsonld(event_listing, city_slug):
    '''
    Save event listing to the database.

    Args:
        event_listing (dict): Event listing data from Eventbrite.
        city_tag (str): City tag to associate with the event listing.
        url (str): URL of the event listing (optional)
    '''
    event = Event().init_from_jsonld(event_listing)
    event.city_slug = city_slug
    event.city_tag = CITIES[city_slug]["name"]
    event.generate_emoji()
    try:
        db.session.add(event)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()


def save_event_from_jsonld_luma(event_listing, city_slug, url=None):
    '''
    Save event listing to the database.

    Args:
        event_listing (dict): Event listing data from Eventbrite.
        city_tag (str): City tag to associate with the event listing.
        url (str): URL of the event listing (optional)
    '''
    event = Event().init_from_jsonld(event_listing)
    print(event)
    event.city_slug = city_slug
    event.city_tag = CITIES[city_slug]["name"]
    if event.url is None and url is not None:
        event.url = url
    else:
        pass
    event.generate_emoji()
    db.session.add(event)
    db.session.commit()

def update_event_from_form(event_id, form):
    event = Event.query.get(event_id)
    event.emoji = form.get('emoji')
    event.name = form.get('name')
    event.start_date = form.get('start_date')
    event.end_date = form.get('end_date')
    event.location_name = form.get('location_name')
    event.street_address = form.get('street_address')
    event.address_locality = form.get('address_locality')
    event.address_region = form.get('address_region')
    event.postal_code = form.get('postal_code')
    event.description = form.get('description')
    event.reviewed = True
    db.session.add(event)
    db.session.commit()

def get_gpt_summary(event: Event):
    print(f"Getting GPT summary for {event.name}")
    summary = gpt_summarize_event(event.description)
    reasoning = summary.get("is_it_climate", "No Reasoning Provided")
    event.gpt_description = summary["summary"]
    event.gpt_emoji = summary["emoji"]
    event.gpt_score = summary["climate_score"]
    print(f"Climate Score: {event.gpt_score}, GPT Emoji: {event.gpt_emoji}, Original Emoji: {event.emoji}")
    print(f"Summary: {event.gpt_description[0:100]}")
    print(f"Rationale: {reasoning}")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print(" ")
    db.session.add(event)
    db.session.commit()
    return event
