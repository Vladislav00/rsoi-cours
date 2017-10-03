import jwt
from django.core.management import BaseCommand

from auth.settings import PRIVATE_KEY


class Command(BaseCommand):
    help = 'Creates service token'

    def handle(self, *args, **options):
        payload = {'Role': 'service'}
        token = jwt.encode(payload, PRIVATE_KEY, algorithm='RS256')
        with open('service_credentials.txt', 'w') as sc:
            sc.write(token.decode())

