import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import csv
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
from unique_site_constants import CitySitemaps, example_datetime_handler
from sqlite3 import IntegrityError
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_unique_event_urls(sitemap, city_slug=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    all_urls = []

    url = sitemap['url']
    details = sitemap  # Instead of 'details', we're using the main 'sitemap' directly.

    print(f"Starting scraping for {url}")

    try:
        print("Sending GET request...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print("Response received. Parsing with BeautifulSoup...")
        soup = BeautifulSoup(response.text, 'html.parser')

        if details['type'] == 'simple':
            print("Parsing with simple selector...")
            anchors = soup.select(details['selector'])
            print(anchors)
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            urls = [base_url + anchor['href'] for anchor in anchors if anchor.has_attr('href')]
            print(f"Found {len(urls)} URLs with simple selector.")

        elif details['type'] == 'js':
            print("JavaScript detected. Launching headless Chrome...")
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            time.sleep(2)
            print("Fetching page source after JS execution...")
            soup_js = BeautifulSoup(driver.page_source, 'html.parser')
            anchors = soup_js.select(details['selector'])
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            print(anchors[0]['href'])
            urls = [base_url + anchor['href'] if anchor.get('href', '').startswith('/') and 'http' not in anchor[
                'href'] else anchor['href'] for anchor in anchors]
            print(f"Found {len(urls)} URLs after JS execution.")
            driver.quit()

        else:
            print(f"Error: Unknown parser type for {url}")

        all_urls.extend([url for url in urls])

    except Exception as e:
        print(f"Error scraping {url}: {e}")

    time.sleep(3)

    # Eliminate duplicates
    unique_urls = list(set(all_urls))
    print(f"Total unique URLs found: {len(unique_urls)}")

    return unique_urls

def process_entry(title, description, datetime_str, address, contact_link, url, sitemap, datetime_handler=None):
    event_link = url
    source = sitemap.get('source', None)

    clean_title = title.replace('\n', ' ')
    clean_description = description.replace('\n', ' ')
    clean_address = address.replace('\n', ' ')
    clean_contact_link = contact_link.replace('\n', ' ')
    clean_event_link = event_link.replace('\n', ' ')

    if datetime_handler and datetime_str:
        start_datetime, end_datetime = datetime_handler(datetime_str)
    else:
        start_datetime, end_datetime = datetime_str, None

    clean_start_datetime = start_datetime.replace('\n', ' ')
    clean_end_datetime = end_datetime.replace('\n', ' ')

    return {
        'title': clean_title,
        'description': clean_description,
        'start_datetime': clean_start_datetime,
        'end_datetime': clean_end_datetime,
        'address': clean_address,
        'event_link': clean_event_link,
        'contact_link': clean_contact_link,
        'source': source
    }

def extract_data_from_soup(soup, selector, multi_select, length=1):
    # Check if selector is None and return an empty list
    if multi_select:
        if not selector:
            return [" "] * length
        elements = soup.select(selector)
        return [el.text for el in elements] if elements else [" "] * length
    else:
        if not selector:
            return " " * length
        element = soup.select_one(selector)
        return element.text if element else " " * length

def custom_length(item):
    return len(item) if isinstance(item, list) else 1 if isinstance(item, str) else None

def extract_listings_from_urls(sitemap, datetime_handler=None, urls=[]):
    rows = []
    entries = []

    multi_select = sitemap.get('multi_select')

    if 'event_container' in sitemap:
        use_selenium = True
    else:
        use_selenium = False

    if 'event_url' in sitemap:
        scrape_url = True
    else:
        scrape_url = False

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    total_urls = len(urls)
    print(f"Starting extraction for {total_urls} URLs...")

    if use_selenium:
        chrome_options = Options()
        #chrome_options.add_argument("--headless=new")
        driver = webdriver.Chrome(options=chrome_options)

    for index, url in enumerate(urls, start=1):
        print(f"Processing URL {index} of {total_urls}: {url}")

        if use_selenium:
            driver.get(url)

            if 'close_button' in sitemap:
                wait = WebDriverWait(driver, 30)  # Wait up to 30 seconds
                button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sitemap.get('close_button'))))
                button.click()

            event_elements = driver.find_elements(By.CSS_SELECTOR, sitemap['event_container'])
            print(f"Found {len(event_elements)} event elements on the page.")
            for event_element in event_elements:
                event_element.click()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, sitemap['title'])))
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                print("Extracted page source after clicking the event element.")
        else:
            try:
                response = requests.get(url, headers=headers)
                if response.status_code != 200:
                    print(f"Failed to retrieve the page {url}. HTTP Code: {response.status_code}")
                    continue
            except Exception as e:
                print(e)
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            print("Extracted page source using BeautifulSoup and requests.")

        titles = extract_data_from_soup(soup, sitemap.get('title'), multi_select)
        descriptions = extract_data_from_soup(soup, sitemap.get('description'), multi_select, custom_length(titles))
        datetimes = extract_data_from_soup(soup, sitemap.get('datetime'), multi_select, custom_length(titles))
        addresses = extract_data_from_soup(soup, sitemap.get('address'), multi_select, custom_length(titles))
        contact_links = extract_data_from_soup(soup, sitemap.get('contact_link'), multi_select, custom_length(titles))
        if scrape_url:
            event_urls = extract_data_from_soup(soup, sitemap.get('event_url'), multi_select,custom_length(titles))

        if multi_select:
            entries.append(titles)
            entries.append(descriptions)
            entries.append(datetimes)
            entries.append(addresses)
            entries.append(contact_links)
            if scrape_url:
                entries.append(event_urls)
            entries = [list(item) for item in zip(*entries)]
            for entry_data in entries:
                if scrape_url:
                    entry = process_entry(*entry_data, sitemap, datetime_handler)
                    print(entry)

                else:
                    entry = process_entry(*entry_data, url, sitemap, datetime_handler)
                    print(entry)

                rows.append(entry)
        else:
            entry_data = [titles, descriptions, datetimes, addresses, contact_links]
            entry = process_entry(*entry_data, url, sitemap, datetime_handler)
            print(entry)
            rows.append(entry)

        print(f"Successfully processed URL {index}: {url}")

    if use_selenium:
        driver.quit()

    print("Converting rows to DataFrame...")
    df = pd.DataFrame(rows)
    print(f"Extraction completed. Processed {len(df)} listings.")

    return df


def df_to_jsonld(df):
    jsonld_data = []

    # No need to read the CSV; we use the columns directly from the DataFrame
    header = df.columns

    for _, entry in df.iterrows():
        event = {
            "@context": "http://schema.org",
            "@type": "Event",
            "name": entry['title'],
            "startDate": entry['start_datetime'],
            "endDate": entry['end_datetime'],
            "location": {
                "@type": "Place",
                "name": entry['address'],
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": entry['address'],
                }
            },
            "description": entry['description'],
            "organizer": {
                "@type": "Organization",
                "url": entry['contact_link']
            },
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "url": entry['event_link']
        }
        jsonld_data.append(event)

    return jsonld_data

def print_city_json_data(slug, datetime_handler):
    sitemaps = CitySitemaps.get_sitemaps_by_slug(slug)

    for sitemap in sitemaps:
        if sitemap.get('multi_select') == False:
            urls = scrape_unique_event_urls(sitemap)
        else:
            urls = [sitemap.get('url')]

        df = extract_listings_from_urls(sitemap, datetime_handler, urls)
        jsons = df_to_jsonld(df)
        for json in jsons:
            print("Here is the JSON:"
                  ""
                  f"{json}")

def print_source_json_data(source, slug, datetime_handler):
    sitemap = CitySitemaps.get_sitemap_by_source_and_slug(source, slug)

    if sitemap.get('multi_select') == False:
        urls = scrape_unique_event_urls(sitemap)
    else:
        urls = [sitemap.get('url')]

    df = extract_listings_from_urls(sitemap, datetime_handler, urls)
    jsons = df_to_jsonld(df)
    for json in jsons:
        print("Here is the JSON:"
              ""
              f"{json}")
        continue

'''
def extract_and_save_by_slug(slug, datetime_handler):
    sitemaps = CitySitemaps.get_sitemaps_by_slug(slug)

    for sitemap in sitemaps:
        if sitemap.get('multi_select') == False:
            urls = scrape_unique_event_urls(sitemap)
        else:
            urls = [sitemap.get('url')]

        df = extract_listings_from_urls(sitemap, datetime_handler, urls)
        jsons = df_to_jsonld(df)
        for json in jsons:
            try:
                save_event_from_jsonld(json, slug)
            except IntegrityError as e:
                print("Entry already exists: " + str(json))
                continue
            except RuntimeError as e:
                print("A runtime error has occurred, likely because this function is being run outside "
                      "of the flask application. Here is the JSON:"
                      ""
                      f"{json}")
                continue

def extract_and_save_by_source_and_slug(source, slug, datetime_handler):
    sitemap = CitySitemaps.get_sitemap_by_source_and_slug(source,slug)

    if sitemap.get('multi_select') == False:
        urls = scrape_unique_event_urls(sitemap)
    else:
        urls = [sitemap.get('url')]

    df = extract_listings_from_urls(sitemap, datetime_handler, urls)
    jsons = df_to_jsonld(df)
    for json in jsons:
        try:
            save_event_from_jsonld(json, slug)
        except IntegrityError as e:
            db.session.rollback()
            print(e)
            print("Entry already exists: " + str(json))
            continue
        except RuntimeError as e:
            print("A runtime error has occurred, likely because this function is being run outside "
                  "of the flask application. Here is the JSON:"
                  ""
                  f"{json}")
            continue
'''


