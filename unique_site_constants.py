import dateparser

def example_datetime_handler(datetime_str):
    start_str, _, end_str = datetime_str.partition('-')
    return start_str.strip(), end_str.strip()

class CitySitemaps:
    ALL_SITEMAPS = [
        {
            'url': 'https://www.climate.columbia.edu/events',
            'type': 'js',
            'selector': 'h2 a',
            'source': 'Columbia',
            'title': 'h2 span',
            'description': 'div.field--name-body',
            'datetime': 'div.event-datetime-info',
            'address': 'div.field--name-field-cu-location',
            'multi_select': False,
            'slug': 'new-york'
        },
        {
            'url': 'https://www.reticenter.org/events/',
            'type': 'js',
            'selector': 'a.eventlist-button',
            'source': 'RETI Center',
            'title': 'h1',
            'description': 'div.eventitem-column-content',
            'datetime': 'ul.event-meta-date-time-container',
            'address': 'ul.event-meta-address-container',
            'multi_select': False,
            'slug': 'new-york'
        },
        {
            'url': 'https://climatemuseum.org/events/',
            'type': 'js',
            'selector': "a.summary-title-link",
            'source': 'Climate Museum',
            'title': 'h1',
            'description': 'div.eventitem-column-content',
            'datetime': 'ul.event-meta-date-time-container',
            'address': 'ul.event-meta-address-container',
            'multi_select': False,
            'slug': 'new-york'
        },
        {
            'url': 'https://nyforcleanpower.org/calendar/',
            'type': 'js',
            'event_container': "div[itemtype='http://schema.org/Event']",
            'close_button': ".pum-close.popmake-close",
            'source': 'NYC For Clean Power',
            'title': 'span.evcal_desc2',
            'description': "div[itemprop='description']",
            'datetime': "div:nth-of-type(4) [itemtype='http://schema.org/Event'] .evo_time p, div:nth-of-type(4) .evo_metarow_time p",
            'address': "div:nth-of-type(4) [itemtype='http://schema.org/Event'] .evo_location div",
            'event_url': 'a.evcal_col50',
            'multi_select': True,
            'slug': 'new-york'
        },
        {
            'url': 'https://waterfrontalliance.org/waterfront-events/',
            'type': 'js',
            'source': 'WaterFront',
            'title': 'h3',
            'description': '.event-description p',
            'datetime': 'p.event-date-time',
            'address': '.event-address p:nth-of-type(1)',
            'multi_select': True,
            'slug': 'new-york'
        },
        {
            'url': 'https://www.weact.org/latest/events/',
            'type': 'js',
            'source': 'WeAct',
            'selector': '#future a.button',
            'title': 'h1',
            'description': 'div.text',
            'datetime': '.obj-eventDateTime span.val',
            'address': 'div:nth-of-type(n+6) span.val',
            'multi_select': False,
            'slug': 'new-york'
        }
    ]

    @staticmethod
    def get_sitemaps_by_slug(slug):
        return [sitemap for sitemap in CitySitemaps.ALL_SITEMAPS if sitemap['slug'] == slug]

    @staticmethod
    def get_sitemap_by_source_and_slug(source, slug):
        for sitemap in CitySitemaps.ALL_SITEMAPS:
            if sitemap['slug'] == slug and sitemap['source'] == source:
                return sitemap
        return None  # Return None if no match found

