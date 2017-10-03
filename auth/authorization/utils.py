import jwt

public = """-----BEGIN PUBLIC KEY-----
MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAJcbqAb6aNYQCFWagLngKAptIs2LfrCa
ZuFU4Qs9RiAvhvgRUBhialP9r3LiRfSVEULIQiiM61bcqMcQgclPBlkCAwEAAQ==
-----END PUBLIC KEY-----"""



def check_authorisation(r):
    authorization = r.META.get('HTTP_AUTHORIZATION', None) or r.COOKIES.get('auth_token', None)
    if authorization is None:
        return None
    try:
        payload = jwt.decode(authorization, public, algorithms=['RS256'])
    except jwt.InvalidTokenError:
        return None
    return payload


def check_role(payload, roles):
    try:
        return payload['Role'] in roles
    except KeyError:
        return False
