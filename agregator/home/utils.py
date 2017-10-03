import jwt
import redis
from django.http import HttpRequest
from rq import Queue

public = """-----BEGIN PUBLIC KEY-----
MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAJcbqAb6aNYQCFWagLngKAptIs2LfrCa
ZuFU4Qs9RiAvhvgRUBhialP9r3LiRfSVEULIQiiM61bcqMcQgclPBlkCAwEAAQ==
-----END PUBLIC KEY-----"""

redis_host = 'localhost'
redis_port = 6379
redis_db = 4


def check_authorisation(r: HttpRequest):
    authorization = r.META.get('HTTP_AUTHORIZATION', None) or r.COOKIES.get('auth_token', None)
    if authorization is None:
        return None
    try:
        payload = jwt.decode(authorization, public, algorithms=['RS256'])
    except jwt.InvalidTokenError:
        return None
    payload['token'] = authorization
    return payload


def check_role(payload, roles):
    try:
        return payload['Role'] in roles
    except KeyError:
        return False


token = None


def get_service_token():
    global token
    if token is None:
        # load cred
        with open("home/service_credentials.txt", "r") as sc:
            token = sc.readline()
    return token


class MyPaginator:
    def __init__(self, page, per_page, count):
        self.start_n = 1 if page > 1 else None
        self.prev_n = page - 1 if page > 1 else None
        self.n = page
        d, m = divmod(count, per_page)
        pages = d if m == 0 else d + 1
        self.next_n = page + 1 if page < pages else None


def queued(func):
    def enq(*args):
        redis_conn = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
        queue = Queue(connection=redis_conn)
        queue.enqueue(func, *args)
    func.enqueue = enq
    return func


