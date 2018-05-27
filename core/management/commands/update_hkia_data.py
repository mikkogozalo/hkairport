from django.core.management.base import BaseCommand
import requests

from core.models import Airline, Lounge, GroundHandling, Airport


class Command(BaseCommand):
    help = 'Create choose one question'


    def handle(self, *args, **options):

        data = requests.get('https://www.hongkongairport.com/iwov-resources/custom/json/airline_en.json').json()

        for external_id, _l in data['airline-lounge'].items():
            print(Lounge.create_or_update_from_json(external_id, _l))

        for external_id, _g in data['ground-handling-agent'].items():
            print(GroundHandling.create_or_update_from_json(external_id, _g))

        for _a in data['airline'].values():
            print(Airline.create_or_update_from_json(_a))

        data = requests.get('https://www.hongkongairport.com/flightinfo-rest/rest/airports').json()
        for _a in data:
            print(Airport.create_or_update_from_json(_a))

        data = requests.get('https://www.hongkongairport.com/flightinfo-rest/rest/airlines').json()
        for _a in data:
            print(Airline.create_or_update_from_jurrasic_json(_a))
