import hashlib
import os
import uuid

import binascii
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from functools import reduce

from authorization.fields import CharNullField


def generate_uuid():
    uid = None
    while uid is None:
        uid = uuid.uuid4()
        try:
            LoyalUser.objects.get(id=uid)
        except ObjectDoesNotExist:
            pass
        else:
            # uid not unique:(
            uid = None
    return uid


class LoyalUser(models.Model):
    id = models.UUIDField(primary_key=True, default=generate_uuid, editable=False)

    name = models.CharField(max_length=128)
    vk_id = CharNullField(max_length=32, null=True, blank=True, unique=True)
    fb_id = CharNullField(max_length=32, null=True, blank=True, unique=True)
    ok_id = CharNullField(max_length=32, null=True, blank=True, unique=True)
    go_id = CharNullField(max_length=32, null=True, blank=True, unique=True)

    login = CharNullField(max_length=32, null=True, blank=True, unique=True)

    password = models.CharField('password', max_length=64)

    salt = models.CharField(max_length=64, blank=True)

    ROLE_CHOICES = (
        ("user", "user"),
        ("manager", "manager"),
        ("fabric", "fabric"),
        ("service", "service")
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")

    refresh_token = models.UUIDField(default=uuid.uuid4)

    def set_password(self, raw_pas):
        salt = os.urandom(32)
        self.salt = binascii.hexlify(salt)
        dk = hashlib.pbkdf2_hmac('sha256', raw_pas.encode('utf-8'), salt, 100000)
        self.password = binascii.hexlify(dk)

    def check_password(self, raw_pas):
        salt = binascii.unhexlify(self.salt)
        dk = hashlib.pbkdf2_hmac('sha256', raw_pas.encode('utf-8'), salt, 100000)
        pas = binascii.hexlify(dk).decode()
        c = map(lambda a, b: a == b, self.password, pas)
        return reduce(lambda a, b: a and b, c, True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.name = self.login
        super(LoyalUser, self).save(*args, **kwargs)

