# Unique Site Scrapers
This repository provides a framework for scraping event information from various unique sites. These sites might not fit common scraping patterns, hence the need for dedicated scripts and configurations.

Main Components
1. Models (models.py)
Defines the data models for events, including attributes such as id, status, emoji, and city_tag.
Provides an EventConstants enumeration for event statuses.
2. Event Services (event_services.py)
Offers utility functions for managing events:
Fetching future events.
Retrieving events by city.
Sorting events by date.
Updating event emojis.
3. Unique Site Constants (unique_site_constants.py)
Contains configurations for web scraping of different event sites in the CitySitemaps class.
Provides the example_datetime_handler utility function to handle datetime strings.
4. Unique Site Services (unique_site_services.py)
Provides services for scraping unique sites.
Uses libraries such as requests, BeautifulSoup, and selenium to facilitate web scraping.
5. Unique Site Services Test (unique_site_services_test.py)
A test or demonstration script to check the output of the scraping and processing functions.
Getting Started
To scrape data from a site, utilize the configurations in unique_site_constants.py and the services in unique_site_services.py.

Further documentation can be found within each individual file for specific functionalities and configurations.
