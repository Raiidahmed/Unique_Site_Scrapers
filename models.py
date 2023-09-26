import random
from datetime import datetime
from enum import Enum

from bs4 import BeautifulSoup
from scraper import db
from scraper.services.constants import EVENTBRITE_CONFIG
from scraper.services.emoji import EMOJIS
from scraper.services.scraping_services import (extract_events_from_json_ld,
                                                fetch_page)


class EventConstants(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"


class Event(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    # Manually set on the Event Review page
    # Can be "approved", "rejected", or "pending"
    status = db.Column(db.String(20), default="pending")
    # Manually set on the Event Review page
    emoji = db.Column(db.String(10))

    # Eventbrite details updated
    details_updated = db.Column(db.Boolean, default=False)
    # manually reviewed
    reviewed = db.Column(db.Boolean, default=False)

    # Set at creation / Update
    city_tag = db.Column(db.String(50))
    city_slug = db.Column(db.String(50))
    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))
    name = db.Column(db.String(100))
    url = db.Column(db.String(200), unique=True, nullable=False)
    image = db.Column(db.String(200))
    low_price = db.Column(db.Float)
    high_price = db.Column(db.Float)
    price_currency = db.Column(db.String(10))
    location_name = db.Column(db.String(100))
    address_country = db.Column(db.String(50))
    address_locality = db.Column(db.String(50))
    address_region = db.Column(db.String(50))
    street_address = db.Column(db.String(200))
    postal_code = db.Column(db.String(20))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    event_attendance_mode = db.Column(db.String(200))
    description = db.Column(db.Text)

    gpt_description = db.Column(db.Text)
    gpt_emoji = db.Column(db.String(10))
    gpt_score = db.Column(db.Float)

    def __init__(self):
        pass

    def init_from_jsonld(self, data):
        self.url = data.get("url")
        self.start_date = data.get("startDate")
        self.end_date = data.get("endDate")
        self.name = data.get("name")
        self.low_price = data.get("offers", {}).get("lowPrice")
        self.high_price = data.get("offers", {}).get("highPrice")
        self.price_currency = data.get("offers", {}).get("priceCurrency")
        self.location_name = data.get("location", {}).get("name")

        image = data.get("image")
        if isinstance(image, dict):
            self.image = data.get("image")
        elif isinstance(image, str):
            self.image = image
        elif isinstance(image, list):
            self.image = image[0]
        else:
            self.image = None

        address = data.get("location", {}).get("address")
        if isinstance(address, str):
            ad = address.split(',')
            if len(ad) < 5:
                raise Exception("Address is not in the expected format")
            # Example: 'Homebound Brew Haus, 800 N Alameda St, Los Angeles, CA 90012, USA'
            # ad[0] = 'Homebound Brew Haus'
            # ad[1] = ' 800 N Alameda St'
            # ad[2] = ' Los Angeles'
            # ad[3] = ' CA 90012'
            # ad[4] = ' USA'
            self.street_address = ad[1].strip()
            self.address_locality = ad[2].strip()

            region_and_postal = ad[3].split(' ')
            self.address_region = region_and_postal[0].strip()
            self.postal_code = region_and_postal[1].strip()

            self.address_country = ad[4].strip()

        elif isinstance(address, dict):
            self.address_country = address.get("addressCountry")
            self.address_locality = address.get("addressLocality")
            self.address_region = address.get("addressRegion")
            self.street_address = address.get("streetAddress")
            self.postal_code = address.get("postalCode")

        self.latitude = data.get("location", {}).get("geo", {}).get("latitude")
        self.longitude = data.get("location", {}).get("geo", {}).get("longitude")


        self.event_attendance_mode = data.get("eventAttendanceMode")
        self.description = data.get("description")
        return self
    
    def to_dict(self):
        return {
            'id': self.id,
            'status': self.status,
            'emoji': self.emoji,
            'city_tag': self.city_tag,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'name': self.name,
            'url': self.url,
            'image': self.image,
            'low_price': self.low_price,
            'high_price': self.high_price,
            'price_currency': self.price_currency,
            'location_name': self.location_name,
            'address_country': self.address_country,
            'address_locality': self.address_locality,
            'address_region': self.address_region,
            'street_address': self.street_address,
            'postal_code': self.postal_code,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'description': self.description,
            'gpt_description': self.gpt_description,
            'gpt_emoji': self.gpt_emoji,
            'gpt_score': self.gpt_score,
        }

    def is_eventbrite(self):
        return "eventbrite" in self.url
    
    def friendly_short_date(self):
        return self.start_datetime().strftime("%a, %b %-d")

    def friendly_long_date(self):
        def suffix(d):
            return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')
        
        start = self.start_datetime()
        end = self.end_datetime()
        if start.date() == end.date():
            return start.strftime(f'%a, %b %-d{suffix(start.day)} from %-I:%M %p') + end.strftime(' to %-I:%M %p')
        else:
            return start.strftime(f'%a, %b %-d{suffix(start.day)} from %-I:%M %p') + end.strftime(' to %a, %b %-d{suffix(end.day)} at %-I:%M %p')

    def friendly_address(self):
        address_strs = []
        if self.location_name is not None and self.location_name != "":
            address_strs.append(self.location_name)
        if self.street_address is not None and self.street_address != "":
            address_strs.append(self.street_address)
        if self.address_locality is not None and self.address_locality != "":
            address_strs.append(self.address_locality)
        if self.address_region is not None and self.address_region != "":
            address_strs.append(self.address_region)

        addr = ", ".join(address_strs)
        return addr.strip().strip(",")



    def start_datetime(self):
        try:
            if len(self.start_date) == len("2023-07-12"):
                self.start_date = self.start_date + "T00:00:00-07:00"
            elif len(self.start_date) == len("2023-07-27T17:00:00.000-07:00"):
                self.start_date = self.start_date.replace(".000", "")
            dt = datetime.strptime(self.start_date, "%Y-%m-%dT%H:%M:%S%z")
            return dt
        except ValueError:
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print("ERROR")
            print(self.start_date)
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")


    def end_datetime(self):
        try:
            if len(self.end_date) == len("2023-07-12"):
                self.end_date = self.end_date + "T00:00:00-07:00"
            elif len(self.end_date) == len("2023-07-27T17:00:00.000-07:00"):
                self.end_date = self.end_date.replace(".000", "")
            dt = datetime.strptime(self.end_date, "%Y-%m-%dT%H:%M:%S%z")
            return dt
        except ValueError:
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print("ERROR")
            print(self.end_date)
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")



    def generate_emoji(self):
        candidate_emojis = []
        emoji_keys = EMOJIS.keys()
        filtered_name = self.name.lower().replace("!", "").replace("?","").replace(":","").replace(",","").replace(".","")
        for keyword in emoji_keys:
            if keyword in filtered_name:
                candidate_emojis.extend(EMOJIS[keyword])
        if len(candidate_emojis) > 0:
            self.emoji = random.choice(candidate_emojis)
        else:
            self.emoji = random.choice(EMOJIS["default"])


