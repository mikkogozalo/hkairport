import time

from django.core.management.base import BaseCommand
import requests

from fr.models import FrLog


class Command(BaseCommand):
    help = 'Create choose one question'

    def handle(self, *args, **options):
        fields = ['mode_s_code',
                  'latitude',
                  'longitude',
                  'bearing',
                  'altitude',
                  'speed',
                  'squawk',
                  'radar',
                  'model',
                  'registration',
                  'timestamp',
                  'origin',
                  'destination',
                  'flight',
                  'unknown_boolean',
                  'vertical_speed',
                  'callsign',
                  'unknown_boolean_2']

        found_hashes = set()

        while True:
            start = time.time()
            while True:
                r = requests.get(
                    'https://data-live.flightradar24.com/zones/fcgi/feed.js?bounds=39.32,-22.94,32.71,-156.80&faa=1&mlat=1&flarm=1&adsb=1&gnd=1&air=1&vehicles=1&estimated=1&maxage=14400&gliders=1&stats=1',
                    headers={'accept': 'application/json, text/javascript, */*; q=0.01',
                             'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36',
                             'referer': 'https://www.flightradar24.com/11.77,117.95/4'})
                if r.status_code == 200:
                    data = r.json()
                    break
                time.sleep(1)
                print('Sleeping for a second, problem fetching with status {}'.format(r.status_code))

            to_delete = ['full_count', 'stats', 'version']
            for _ in to_delete:
                del data[_]

            data_list = list(data.values())
            data_list = [dict(zip(fields, _)) for _ in data_list]

            this_set_hash = set()

            ctr = 0

            for _ in data_list:
                try:
                    hash = FrLog.hash_feed(_)
                    this_set_hash.add(hash)
                    if hash in found_hashes:
                        continue
                    FrLog.create_from_feed(hash, _)
                    ctr += 1
                except:
                    pass

            found_hashes = this_set_hash

            end = time.time()
            print('Finished cycle with {} new logs in {}s'.format(ctr, end - start))
            time.sleep(10 - ((end - start) % 10))

