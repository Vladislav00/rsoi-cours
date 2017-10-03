from django.core.management import BaseCommand

from authorization.models import LoyalUser

import random
import string

class Command(BaseCommand):
    help = 'Creates superuser'

    def handle(self, *args, **options):
        passchars = string.ascii_letters+string.digits
        #create manager1
        m = LoyalUser.objects.create(login='admin', role='manager')
        p = "".join([random.choice(passchars) for _ in range(15)])
        m.set_password(p)
        m.save()
        print("Created user '{}'\n password '{}'\n".format("admin", p))

