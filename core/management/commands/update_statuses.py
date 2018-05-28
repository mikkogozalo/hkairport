import time
import pytz
from itertools import product
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
import requests

from core.models import Departure, Arrival


class Command(BaseCommand):
    help = 'Create choose one question'


    def handle(self, *args, **options):
        while True:
            start = time.time()

            url = 'https://www.hongkongairport.com/flightinfo-rest/rest/flights?span=2&date={}&lang=en&cargo={}&arrival={}'
            perms = product(['true', 'false'], ['true', 'false'])
            for cargo, arrival in perms:
                date = (timezone.now().astimezone(pytz.timezone('Asia/Manila')) - timedelta(days=1)).strftime('%Y-%m-%d')
                data = requests.get(url.format(date, cargo, arrival)).json()
                cls = Arrival if arrival == 'true' else Departure

                for d in data:
                    date = d['date']
                    for flight in d['list']:
                        try:
                            cls.create_or_update_from_json(date, flight, is_cargo=cargo == 'true', print_it=True)
                        except:
                            pass
            end = time.time()
            print('Done in {}s'.format(end - start))
            time.sleep(30 - (30 % (end - start)))