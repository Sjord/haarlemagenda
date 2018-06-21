import requests
from bs4 import BeautifulSoup
import json
from icalendar import Calendar, Event
import dateutil.parser
from datetime import datetime


class EventData:
    def __init__(self, data):
        self.summary = data[0]['name']
        self.description = data[0]['description']

        dates = [dateutil.parser.parse(d['startDate']) for d in data]
        self.start = min(dates)
        self.end = max(dates)


calendar = Calendar()
calendar.add('summary', "Haarlem")
calendar.add('prodid', '-//Haarlem agenda//Haarlem agenda//')
calendar.add('version', '2.0')

mainpage = "https://www.haarlemmarketing.nl/uitagenda"
root = "https://www.haarlemmarketing.nl"
events_page = "https://www.haarlemmarketing.nl/uitagenda/overzicht?calendar_range=&search=&keyword=Evenementen"

res = requests.get(events_page)
soup = BeautifulSoup(res.text, "html.parser")
links = soup.select("a.tile__link-overlay")
urls = [root + a['href'] for a in links if a['href'].startswith("/uitagenda/overzicht/")]
for url in urls:
    print(url)
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    data_tag = soup.find("script", type="application/ld+json")
    data = EventData(json.loads(data_tag.text))

    event = Event()
    event.add('summary', data.summary)
    event.add('dtstart', data.start.date())
    event.add('dtend', data.end.date())
    event.add('dtstamp', datetime.now())
    event.add('description', data.description)
    calendar.add_component(event)

with open('haarlem.ics', 'wb') as fp:
    fp.write(calendar.to_ical())
