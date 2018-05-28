import pytz
import hashlib
from datetime import datetime, timedelta

from django.db import models


class FrLog(models.Model):
    class Meta:
        db_table = 'fr_log'

    flight = models.CharField(max_length=16, blank=True, null=True, db_index=True)
    registration = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    model = models.CharField(max_length=16, blank=True, null=True, db_index=True)
    callsign = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    timestamp = models.DateTimeField(db_index=True)
    origin = models.CharField(max_length=3, blank=True, null=True, db_index=True)
    destination = models.CharField(max_length=3, blank=True, null=True, db_index=True)

    latitude = models.FloatField()
    longitude = models.FloatField()
    bearing = models.IntegerField(blank=True, null=True)
    altitude = models.IntegerField(blank=True, null=True)
    vertical_speed = models.IntegerField(blank=True, null=True)
    speed = models.IntegerField(blank=True, null=True)
    radar = models.CharField(max_length=64, blank=True, null=True)

    mode_s_code = models.CharField(max_length=255, blank=True, null=True)
    squawk = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    unknown_boolean = models.BooleanField()
    unknown_boolean_2 = models.BooleanField()

    hash = models.CharField(max_length=32, db_index=True)

    @classmethod
    def create_from_feed(cls, hash, feed):
        feed = feed.copy()
        log = cls.objects.filter(hash=hash).first()
        if log:
            return log, False

        last_log: FrLog = cls.objects.filter(registration=feed['registration']).order_by('-timestamp').first()
        feed['timestamp'] = datetime.fromtimestamp(feed['timestamp'], pytz.timezone('Asia/Manila'))
        if last_log:
            if (
                (feed['timestamp'] - last_log.timestamp).total_seconds() <= 60 and
                abs(last_log.vertical_speed) == 0 and abs(feed['vertical_speed']) == 0 and  # Cruising
                feed['altitude'] > 1000  # Above 1000ft
            ):
                return last_log, False

        log = FrLog()
        for k, v in feed.items():
            setattr(log, k, v)
        log.hash = hash
        log.save()
        return log, True

    @classmethod
    def hash_feed(cls, feed):
        keys = sorted(feed.keys())
        concatenate = ''
        for _ in keys:
            concatenate = concatenate + str(feed[_])

        return hashlib.md5(concatenate.encode('utf-8')).hexdigest()
