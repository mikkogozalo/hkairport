from dateutil.parser import parse
from datetime import timedelta

import pytz
from itertools import product

from django.core.management.base import BaseCommand
from django.utils import timezone
import requests

from core.models import Departure, Arrival


class Command(BaseCommand):
    help = 'Create choose one question'


    def handle(self, *args, **options):

        _date = parse('2018-04-08').astimezone(pytz.timezone('Asia/Manila'))

        while _date.date() != timezone.now().astimezone(pytz.timezone('Asia/Manila')).date():
            url = 'https://www.hongkongairport.com/flightinfo-rest/rest/flights?span=1&date={}&lang=en&cargo={}&arrival={}'
            perms = product(['true', 'false'], ['true', 'false'])
            date = _date.strftime('%Y-%m-%d')
            _date += timedelta(days=1)
            print('Fetching for date {}'.format(date))
            for cargo, arrival in perms:
                data = requests.get(url.format(date, cargo, arrival)).json()
                cls = Arrival if arrival == 'true' else Departure

                for d in data:
                    date = d['date']
                    for flight in d['list']:
                        try:
                            cls.create_or_update_from_json(date, flight, is_cargo=cargo == 'true')
                        except:
                            pass
