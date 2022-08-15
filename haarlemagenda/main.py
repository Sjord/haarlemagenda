import requests
from bs4 import BeautifulSoup
import json
from icalendar import Calendar, Event
import dateutil.parser
from datetime import datetime, timedelta
import locale


class EventData:
    def __init__(self, data):
        self.summary = data[0]['name']
        self.description = data[0]['description']
        self.image = data[0].get('image')

        dates = [dateutil.parser.parse(d['startDate']) for d in data]
        self.start = min(dates)
        self.end = max(dates)
        self.duration = self.end - self.start


def parse_date(date_text):
    dayofweek, _ = date_text.split(' ', 1)
    yearless = datetime.strptime(date_text, "%A %d %B")
    current_year = datetime.now().date().year
    for year in range(current_year - 2, current_year + 2):
        attempt = yearless.replace(year=year)
        if attempt.strftime("%A") == dayofweek.lower():
            return attempt
    raise ValueError(date_text)

locale.setlocale(locale.LC_ALL, "nl_NL")    

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

events_page = "https://www.visithaarlem.com/uitagenda/"

res = requests.get(events_page)
soup = BeautifulSoup(res.text, "html.parser")
links = soup.select("div[class^='featured'] a[href]")
urls = [a['href'] for a in links if a['href'].startswith("https://www.visithaarlem.com/evenement/")]
for url in urls:
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    summary = soup.select_one("meta[property='og:title']")["content"]
    description = soup.select_one("meta[property='og:description']")["content"]
    image = None # soup.select_one("meta[property='og:image']")["content"]
    summary, _ = summary.split(" | ")

    dates = soup.select("h5:not([class])")
    if 0 < len(dates) < 14:
        dates = [parse_date(d.text) for d in dates]
        start_date = min(dates)
        end_date = max(dates)

        if summary in start_dates:
            start_date = min(start_date, start_dates[summary])

        event = Event()
        event.add('summary', summary)
        event.add('dtstart', start_date)
        event.add('dtend', end_date)
        event.add('dtstamp', datetime.now())
        event.add('description', description)
        if image:
            event.add('image', image, parameters={'VALUE': 'URI'})
        calendar.add_component(event)

with open('haarlem.ics', 'wb') as fp:
    fp.write(calendar.to_ical())
