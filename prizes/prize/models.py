import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.db import models


def generate_uuidp():
    uid = None
    while uid is None:
        uid = uuid.uuid4()
        try:
            Prize.objects.get(id=uid)
        except ObjectDoesNotExist:
            pass
        else:
            # uid not unique:(
            uid = None
    return uid


def generate_uuido():
    uid = None
    while uid is None:
        uid = uuid.uuid4()
        try:
            Prize.objects.get(id=uid)
        except ObjectDoesNotExist:
            pass
        else:
            # uid not unique:(
            uid = None
    return uid


class Prize(models.Model):
    id = models.UUIDField(primary_key=True, default=generate_uuidp, editable=False)
    title = models.CharField(max_length=128)
    pic = models.ImageField(default='no-img.jpg')
    cost = models.PositiveIntegerField(default=0)
    provider = models.CharField(max_length=128)


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=generate_uuido, editable=False)
    prize = models.UUIDField()
    user = models.UUIDField()
    user_contacts = models.CharField(max_length=512)
