import requests
from bs4 import BeautifulSoup
import json
from icalendar import Calendar, Event
import dateutil.parser
from datetime import datetime, timedelta


class EventData:
    def __init__(self, data):
        self.summary = data[0]['name']
        self.description = data[0]['description']

        dates = [dateutil.parser.parse(d['startDate']) for d in data]
        self.start = min(dates)
        self.end = max(dates)
        self.duration = self.end - self.start


# Copy start dates from existing haarlem.ics
start_dates = {}
try:
    with open('haarlem.ics', 'rb') as fp:
        old_calendar = Calendar.from_ical(fp.read())
        for ev in old_calendar.walk("VEVENT"):
            start_date = ev['dtstart'].dt
            summary = ev['summary']
            start_dates[summary] = start_date
except FileNotFoundError:
    print("haarlem.ics not found")


calendar = Calendar()
calendar.add('summary', "Haarlem")
calendar.add('prodid', '-//Haarlem agenda//Haarlem agenda//')
calendar.add('version', '2.0')

mainpage = "https://www.visithaarlem.com/nl/uitagenda"
root = "https://www.visithaarlem.com"
events_page = "https://www.visithaarlem.com/nl/uitagenda/overzicht?calendar_range=&keyword=Evenementen&search="

res = requests.get(events_page)
soup = BeautifulSoup(res.text, "html.parser")
links = soup.select("a.tile__link-overlay")
urls = [root + a['href'] for a in links if a['href'].startswith("/nl/uitagenda/overzicht/")]
for url in urls:
    print(url)
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    data_tag = soup.find("script", type="application/ld+json")
    data = EventData(json.loads(data_tag.text))

    if data.duration < timedelta(days=14):
        summary = data.summary
        start_date = data.start.date()
        if summary in start_dates:
            start_date = min(start_date, start_dates[summary])

        event = Event()
        event.add('summary', summary)
        event.add('dtstart', start_date)
        event.add('dtend', data.end.date())
        event.add('dtstamp', datetime.now())
        event.add('description', data.description)
        calendar.add_component(event)

with open('haarlem.ics', 'wb') as fp:
    fp.write(calendar.to_ical())
