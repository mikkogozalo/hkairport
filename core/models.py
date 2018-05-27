import re

from dateutil.parser import parse
from django.db import models
from django.utils import timezone


class ShortNamedModel(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(max_length=16, db_index=True)


class NamedModel(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(max_length=255)


class ChineseNamedModel(models.Model):
    class Meta:
        abstract = True

    name_traditional = models.CharField(max_length=255, blank=True, null=True)
    name_simplified = models.CharField(max_length=255, blank=True, null=True)


class Airport(NamedModel, ChineseNamedModel):
    class Meta:
        db_table = 'airport'

    icao = models.CharField(max_length=4, unique=True, blank=True, null=True, db_index=True)
    iata = models.CharField(max_length=3, unique=True, db_index=True)
    country = models.CharField(max_length=2, db_index=True, blank=True, null=True)

    departures = models.ManyToManyField('Departure', through='DepartureDestination')
    arrivals = models.ManyToManyField('Arrival', through='ArrivalOrigin')

    def __str__(self):
        return self.name

    @classmethod
    def get_by_iata(cls, iata):
        airport = cls.objects.filter(iata=iata).first()
        if not airport:
            airport = cls()
            airport.iata = iata
            airport.save()
        return airport


    @classmethod
    def get_by_icao(cls, icao):
        return cls.objects.filter(iata=icao).first()

    @classmethod
    def create_or_update_from_json(cls, json):
        airport = cls.objects.filter(iata=json['code']).first()
        if not airport:
            airport = cls(iata=json['code'])

        airport.country = json.get('country')
        airport.name = json['description'][0]
        airport.name_traditional = json['description'][1]
        airport.name_simplified = json['description'][2]
        airport.save()
        return airport


class Terminal(ShortNamedModel):
    class Meta:
        db_table = 'terminal'

    full_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.slug

    @classmethod
    def get_terminal(cls, t):
        terminal = cls.objects.filter(name=t).first()
        if not terminal:
            terminal = cls(name=t)
            terminal.save()
        return terminal


class Airline(NamedModel, ChineseNamedModel):
    class Meta:
        db_table = 'airline'

    icao = models.CharField(max_length=3, unique=True, db_index=True)
    iata = models.CharField(max_length=2, db_index=True, blank=True, null=True)


    terminal = models.ForeignKey('Terminal', on_delete=models.CASCADE, blank=True, null=True)
    ground_handling = models.ForeignKey('GroundHandling', on_delete=models.CASCADE, blank=True, null=True)

    phone_enquiry = models.CharField(max_length=32, blank=True, null=True)
    phone_reservation = models.CharField(max_length=32, blank=True, null=True)

    url = models.URLField(max_length=255, blank=True, null=True)

    aisles = models.ManyToManyField('Aisle', through='AirlineAisle')
    transfer_desks = models.ManyToManyField('TransferDesk', through='AirlineTransferDesk')
    lounges = models.ManyToManyField('Lounge', through='AirlineLounge')

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_by_iata(cls, iata):
        return cls.objects.filter(iata=iata).first()

    @classmethod
    def get_by_icao(cls, icao):
        return cls.objects.filter(iata=icao).first()

    @classmethod
    def create_or_update_from_jurrasic_json(cls, json):
        airport = cls.objects.filter(icao=json['code']).first()
        if not airport:
            airport = cls(icao=json['code'])

        airport.name = json['description'][0]
        airport.name_traditional = json['description'][1]
        airport.name_simplified = json['description'][2]
        airport.save()
        return airport

    @classmethod
    def create_or_update_from_json(cls, json):
        MAPPING = {
            'icao-3': 'icao',
            'iata-2': 'iata',
            'website-url': 'url',
            'name': 'name'
        }
        airline = cls.objects.filter(icao=json['icao-3']).first()
        if airline is None:
            airline = cls()

        for json_k, obj_k in MAPPING.items():
            val = json.get(json_k, '').strip()
            if val:
                setattr(airline, obj_k, val)

        all_names = json.get('all-names', [])
        if len(all_names) >= 2:
            airline.name_traditional = all_names[1].strip()
        if len(all_names) >= 3:
            airline.name_simplified = all_names[2].strip()

        phone_enquiry = (json.get('enquiry', [{'phone': ''}]) or [{'phone': ''}])[0].get('phone')
        if phone_enquiry:
            airline.phone_enquiry = phone_enquiry

        phone_reservations = (json.get('reservations', [{'phone': ''}]) or [{'phone': ''}])[0].get('phone')
        if phone_reservations:
            airline.phone_reservation = phone_reservations

        if json['terminal']:
            airline.terminal = Terminal.get_terminal(json['terminal'])

        ground_handling = json.get('ground-handling-agent', [""])[0]
        if ground_handling:
            airline.ground_handling = GroundHandling.get_by_slug(ground_handling)

        airline.save()

        for a in json.get('aisle', []):
            if a:
                aisle = Aisle.get_aisle(a)
                AirlineAisle.objects.get_or_create(airline=airline, aisle=aisle)

        for t in json.get('transfer', []):
            if t and t not in ['NA']:
                transfer_desk = TransferDesk.get_transfer_desk(a)
                AirlineTransferDesk.objects.get_or_create(airline=airline, transfer_desk=transfer_desk)


        for l in json.get('airline-lounge', []):
            if l:
                lounge = Lounge.get_by_external_id(l)
                if lounge:
                    AirlineLounge.objects.get_or_create(airline=airline, lounge=lounge)

        return airline


class Aisle(ShortNamedModel):
    class Meta:
        db_table = 'aisle'

    airlines = models.ManyToManyField('Airline', through='AirlineAisle')
    departures = models.ManyToManyField('Departure', through='DepartureAisle')

    def __str__(self):
        return self.name

    @classmethod
    def get_aisle(cls, aisle):
        a = cls.objects.filter(name=aisle).first()
        if not a:
            a = cls(name=aisle)
            a.save()
        return a


class AirlineAisle(models.Model):
    class Meta:
        db_table = 'airline_aisle'
        unique_together = ['airline', 'aisle']

    airline = models.ForeignKey('Airline', on_delete=models.CASCADE)
    aisle = models.ForeignKey('Aisle', on_delete=models.CASCADE)


class TransferDesk(ShortNamedModel):
    class Meta:
        db_table = 'transfer_desk'

    airlines = models.ManyToManyField('Airline', through='AirlineTransferDesk')

    def __str__(self):
        return self.name

    @classmethod
    def get_transfer_desk(cls, t):
        a = cls.objects.filter(name=t).first()
        if not a:
            a = cls(name=t)
            a.save()
        return a


class AirlineTransferDesk(models.Model):
    class Meta:
        db_table = 'airline_transfer_desk'
        unique_together = ['airline', 'transfer_desk']

    airline = models.ForeignKey('Airline', on_delete=models.CASCADE)
    transfer_desk = models.ForeignKey('TransferDesk', on_delete=models.CASCADE)


class Lounge(NamedModel):
    class Meta:
        db_table = 'lounge'

    external_id = models.CharField(max_length=64, db_index=True)
    opening_hours = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)

    airlines = models.ManyToManyField('Airline', through='AirlineLounge')

    def __str__(self):
        return self.name

    @classmethod
    def create_or_update_from_json(cls, external_id, json):
        MAPPING = {
            'name': 'name',
            'opening-hour': 'opening_hours',
            'location': 'location',
            'remark': 'remark'
        }
        lounge = cls.objects.filter(external_id=external_id).first()
        if lounge is None:
            lounge = cls(external_id=external_id)

        for json_k, obj_k in MAPPING.items():
            val = json.get(json_k, '').strip()
            if val:
                setattr(lounge, obj_k, val)

        lounge.save()

        for a in json.get('telephone', []):
            p = a.get('phone')
            if p:
                LoungePhone.objects.get_or_create(lounge=lounge, phone=p)

        for a in json.get('fax', []):
            f = a.get('fax')
            if f:
                LoungePhone.objects.get_or_create(lounge=lounge, phone=f, is_fax=True)

        return lounge

    @classmethod
    def get_by_external_id(cls, external_id):
        return Lounge.objects.filter(external_id=external_id).first()


class LoungePhone(models.Model):
    class Meta:
        db_table = 'lounge_phone'
        unique_together = ['lounge', 'phone']

    lounge = models.ForeignKey('Lounge', related_name='phones', on_delete=models.CASCADE)
    phone = models.CharField(max_length=64)
    is_fax = models.BooleanField(default=False)

    def __str__(self):
        return self.phone

    @classmethod
    def get_or_create(cls, lounge, phone, is_fax=False):
        return cls.objects.get_or_create(lounge=lounge, phone=phone, is_fax=is_fax)[0]


class AirlineLounge(models.Model):
    class Meta:
        db_table = 'airline_lounge'
        unique_together = ['airline', 'lounge']

    airline = models.ForeignKey('Airline', on_delete=models.CASCADE)
    lounge = models.ForeignKey('Lounge', on_delete=models.CASCADE)


class GroundHandling(NamedModel):
    class Meta:
        db_table = 'ground_handling'

    external_id = models.CharField(max_length=64, db_index=True)
    slug = models.CharField(max_length=64, db_index=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_by_slug(cls, slug):
        return cls.objects.filter(slug=slug).first()

    @classmethod
    def create_or_update_from_json(cls, external_id, json):
        MAPPING = {
            'name': 'slug',
            'fullname': 'name',
        }
        ground_handling = cls.objects.filter(external_id=external_id).first()
        if ground_handling is None:
            ground_handling = cls(external_id=external_id)

        for json_k, obj_k in MAPPING.items():
            val = json.get(json_k, '').strip()
            if val:
                setattr(ground_handling, obj_k, val)

        ground_handling.save()
        return ground_handling


class FlightNumber(models.Model):
    class Meta:
        db_table = 'flight_number'

    airline = models.ForeignKey('Airline', on_delete=models.CASCADE)
    airline_letters = models.CharField(max_length=2)
    number = models.CharField(max_length=5)
    number_ordering = models.IntegerField()
    departures = models.ManyToManyField('Departure', through='DepartureFlightNumber')
    arrivals = models.ManyToManyField('Arrival', through='ArrivalFlightNumber')

    @classmethod
    def get_flight(cls, flight_no):
        flight_no_str = flight_no['no']
        flight_no_str = flight_no_str.split(' ')
        airline = Airline.objects.filter(icao=flight_no['airline']).first()
        if not airline:
            airline = Airline(icao=flight_no['airline'], iata=flight_no_str[0])
            airline.name = airline.icao
            airline.save()
        if airline.iata is None:
            airline.iata = flight_no_str[0]
            airline.save()
        number = flight_no_str[1]
        flight_number = cls.objects.filter(airline=airline, number=number).first()
        if not flight_number:
            flight_number = FlightNumber(airline=airline, number=number,
                                         number_ordering=int(re.search(r'(\d+)', number).group(1)),
                                         airline_letters=flight_no_str[0])
            flight_number.save()
        return flight_number

    def __str__(self):
        return '{} {}'.format(self.airline.iata, self.number)


class Gate(ShortNamedModel):
    class Meta:
        db_table = 'gate'

    def __str__(self):
        return self.name

    @classmethod
    def get_gate(cls, gate):
        return Gate.objects.get_or_create(name=gate)[0]


class Stand(ShortNamedModel):
    class Meta:
        db_table = 'stand'

    def __str__(self):
        return self.name

    @classmethod
    def get_stand(cls, stand):
        return Stand.objects.get_or_create(name=stand)[0]


class BaggageReclaim(ShortNamedModel):
    class Meta:
        db_table = 'baggage_reclaim'

    @classmethod
    def get_baggage_reclaim(cls, baggage_reclaim):
        return BaggageReclaim.objects.get_or_create(name=baggage_reclaim)[0]


class Hall(ShortNamedModel):
    class Meta:
        db_table = 'hall'

    @classmethod
    def get_hall(cls, hall):
        return Hall.objects.get_or_create(name=hall)[0]


class Departure(models.Model):
    class Meta:
        db_table = 'departure'

    flight_numbers = models.ManyToManyField('FlightNumber', through='DepartureFlightNumber')
    destinations = models.ManyToManyField('Airport', through='DepartureDestination')
    terminal = models.ForeignKey('Terminal', related_name='departures', on_delete=models.CASCADE, blank=True, null=True)
    aisles = models.ManyToManyField('Aisle', through='DepartureAisle')
    gate = models.ForeignKey('Gate', blank=True, null=True, on_delete=models.CASCADE)
    schedule = models.DateTimeField()
    actual = models.DateTimeField(blank=True, null=True)
    latest_status = models.ForeignKey('DepartureStatus', related_name='latest', on_delete=models.CASCADE, blank=True, null=True)
    is_cargo = models.BooleanField(default=False)

    @classmethod
    def create_or_update_from_json(cls, date, json, is_cargo=False):
        created = False
        departure_flight_number = DepartureFlightNumber.objects.filter(
            departure__schedule__date=date,
            flight_number__airline__icao=json['flight'][0]['airline'],
            flight_number__number=json['flight'][0]['no'].split(' ')[-1]
        ).distinct().first()
        if departure_flight_number:
            departure = departure_flight_number.departure
            if departure.latest_status and departure.latest_status.status_code == 'DA':
                return departure
        else:
            departure = Departure()
            created = True
        terminal = json.get('terminal')
        if terminal:
            departure.terminal = Terminal.get_terminal(terminal)
        gate = json.get('gate')
        if gate:
            departure.gate = Gate.get_gate(gate)
        departure.schedule = timezone.make_aware(parse(date + ' ' + json.get('time')))
        departure.is_cargo = is_cargo
        departure.save()
        if created:
            for i, flight_no in enumerate(json.get('flight'), start=1):
                flight_number = FlightNumber.get_flight(flight_no)
                DepartureFlightNumber.objects.get_or_create(
                    departure=departure,
                    flight_number=flight_number,
                    defaults={'order': i}
                )
            for destination in json.get('destination'):
                destination = Airport.get_by_iata(destination)
                DepartureDestination.objects.get_or_create(
                    departure=departure,
                    destination=destination
                )
        for aisle in list(json.get('aisle', '')):
            aisle = Aisle.get_aisle(aisle)
            DepartureAisle.objects.get_or_create(departure=departure, aisle=aisle)

        status = json.get('status')
        status_code = json.get('statusCode')

        latest_status: DepartureStatus = departure.statuses.order_by('-created').first()
        if status and (not latest_status or latest_status.status != status or latest_status.status_code != status_code):
                d = DepartureStatus(
                    departure=departure,
                    status_code=status_code,
                    status=status
                )
                d.save()
                departure.latest_status = d
                departure.save()
                print(d)

        return departure

    def __str__(self):
        text = 'DEP: {} {}'.format(self.schedule.strftime('%m/%d %H:%M'), ", ".join(str(_) for _ in self.flight_numbers.all()))
        return text


class DepartureFlightNumber(models.Model):
    class Meta:
        db_table = 'departure_flight_number'
        unique_together = ['departure', 'flight_number']

    departure = models.ForeignKey('Departure', on_delete=models.CASCADE)
    flight_number = models.ForeignKey('FlightNumber', on_delete=models.CASCADE)
    order = models.IntegerField(default=1)


class DepartureAisle(models.Model):
    class Meta:
        db_table = 'departure_aisle'
        unique_together = ['departure', 'aisle']

    departure = models.ForeignKey('Departure', on_delete=models.CASCADE)
    aisle = models.ForeignKey('Aisle', on_delete=models.CASCADE)


class DepartureDestination(models.Model):
    class Meta:
        db_table = 'departure_destination'
        unique_together = ['departure', 'destination']

    departure = models.ForeignKey('Departure', on_delete=models.CASCADE)
    destination = models.ForeignKey('Airport', on_delete=models.CASCADE)


class DepartureStatus(models.Model):
    class Meta:
        db_table = 'departure_status'

    departure = models.ForeignKey('Departure', related_name='statuses', on_delete=models.CASCADE)
    status_code = models.CharField(max_length=2)
    status = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{}: {}'.format(self.departure, self.status)


class Arrival(models.Model):
    class Meta:
        db_table = 'arrival'

    flight_numbers = models.ManyToManyField('FlightNumber', through='ArrivalFlightNumber')
    origins = models.ManyToManyField('Airport', through='ArrivalOrigin')
    stand = models.ForeignKey('Stand', related_name='arrivals', blank=True, null=True, on_delete=models.CASCADE)
    baggage_reclaim = models.ForeignKey('BaggageReclaim', related_name='arrivals', on_delete=models.CASCADE, blank=True, null=True)
    hall = models.ForeignKey('Hall', blank=True, null=True, on_delete=models.CASCADE)
    schedule = models.DateTimeField()
    actual = models.DateTimeField(blank=True, null=True)
    latest_status = models.ForeignKey('ArrivalStatus', related_name='latest', on_delete=models.CASCADE, blank=True, null=True)
    is_cargo = models.BooleanField(default=False)

    @classmethod
    def create_or_update_from_json(cls, date, json, is_cargo=False):
        created = False
        arrival_flight_number = ArrivalFlightNumber.objects.filter(
            arrival__schedule__date=date,
            flight_number__airline__icao=json['flight'][0]['airline'],
            flight_number__number=json['flight'][0]['no'].split(' ')[-1]
        ).distinct().first()
        if arrival_flight_number:
            arrival = arrival_flight_number.arrival
            if arrival.latest_status and arrival.latest_status.status_code == 'ON':
                return arrival
        else:
            arrival = Arrival()
            created = True
        stand = json.get('stand')
        if stand:
            arrival.stand = Stand.get_stand(stand)
        hall = json.get('hall')
        if hall:
            arrival.hall = Hall.get_hall(hall)
        baggage_reclaim = json.get('baggage')
        if baggage_reclaim:
            arrival.baggage_reclaim = BaggageReclaim.get_baggage_reclaim(baggage_reclaim)
        arrival.schedule = timezone.make_aware(parse(date + ' ' + json.get('time')))
        arrival.is_cargo = is_cargo
        arrival.save()
        if created:
            for i, flight_no in enumerate(json.get('flight'), start=1):
                flight_number = FlightNumber.get_flight(flight_no)
                ArrivalFlightNumber.objects.get_or_create(
                    arrival=arrival,
                    flight_number=flight_number,
                    defaults={'order': i}
                )
            for origin in json.get('origin'):
                origin = Airport.get_by_iata(origin)
                ArrivalOrigin.objects.get_or_create(
                    arrival=arrival,
                    origin=origin
                )

        status = json.get('status')
        status_code = json.get('statusCode')

        latest_status: ArrivalStatus = arrival.statuses.order_by('-created').first()
        if status and (not latest_status or latest_status.status != status or latest_status.status_code != status_code):
                d = ArrivalStatus(
                    arrival=arrival,
                    status_code=status_code,
                    status=status
                )
                d.save()
                arrival.latest_status = d
                arrival.save()
                print(d)
        return arrival

    def __str__(self):
        text = 'ARR: {} {}'.format(self.schedule.strftime('%m/%d %H:%M'), ", ".join(str(_) for _ in self.flight_numbers.all()))
        return text


class ArrivalFlightNumber(models.Model):
    class Meta:
        db_table = 'arrival_flight_number'
        unique_together = ['arrival', 'flight_number']

    arrival = models.ForeignKey('Arrival', on_delete=models.CASCADE)
    flight_number = models.ForeignKey('FlightNumber', on_delete=models.CASCADE)
    order = models.IntegerField(default=1)


class ArrivalOrigin(models.Model):
    class Meta:
        db_table = 'arrival_origin'
        unique_together = ['arrival', 'origin']

    arrival = models.ForeignKey('Arrival', on_delete=models.CASCADE)
    origin = models.ForeignKey('Airport', on_delete=models.CASCADE)


class ArrivalStatus(models.Model):
    class Meta:
        db_table = 'arrival_status'

    arrival = models.ForeignKey('Arrival', related_name='statuses', on_delete=models.CASCADE)
    status_code = models.CharField(max_length=2)
    status = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{}: {}'.format(self.arrival, self.status)


def status_update_callback(status):
    if status.status_code in ['LA', '']:
        pass
