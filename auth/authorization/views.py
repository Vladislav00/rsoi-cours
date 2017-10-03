import base64
import datetime
import json
import random
import string
import urllib
import urllib.parse
import uuid
from http import client

import jwt
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from auth.settings import PRIVATE_KEY
from authorization.models import LoyalUser
from authorization.utils import check_authorisation, check_role


def create_token(usr):
    payload = {'Username': usr.name,
               'Id': usr.id.hex,
               'Role': usr.role,
               'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)}
    return jwt.encode(payload, PRIVATE_KEY, algorithm='RS256')


def extract_auth_data(body):
    try:
        data = json.loads(body.decode("utf-8"))
        login = data['login']
        pas = data['password']
    except json.JSONDecodeError:
        # wrong data
        return None, None
    except KeyError:
        # wrong data
        return None, None
    return login, pas


class AuthError(Exception):
    def __init__(self, error):
        super().__init__()
        self.error = error


def process_error(error):
    return HttpResponseRedirect("/auth/complete?error=" + error.error.replace(" ", "_"))


class Register(View):
    def post(self, request):
        login, pas = extract_auth_data(request.body)
        if login is None:
            return HttpResponse(status=400)
        try:
            LoyalUser.objects.get(login=login)
        except ObjectDoesNotExist:
            pass
        else:
            return process_error(AuthError("login already in use"))
        if len(pas) < 6:
            return process_error(AuthError("password too short"))
        obj = LoyalUser.objects.create(login=login)
        obj.set_password(pas)
        obj.save()
        return HttpResponse(status=200)


class RegisterFabric(View):
    def post(self, request, count):
        auth = check_authorisation(request)
        if auth is None:
            return HttpResponse(status=401)
        if not check_role(auth, ['manager']):
            return HttpResponse(status=403)
        fabrics = LoyalUser.objects.filter(login__regex=r'^Fabric[0-9A-Z]{2}$').all()
        # big but very rare operation
        used = set(int(f.login[-2:], 36) for f in fabrics)
        possible = set(range(36 * 36))
        possible = list(possible.difference(used))
        chars = string.ascii_letters + string.digits

        def its36(num):
            digs = string.digits + string.ascii_uppercase
            d, m = divmod(num, 36)
            return digs[d] + digs[m]

        res = []
        for c in range(int(count)):
            if len(possible) == 0:
                break
            num = random.choice(possible)
            possible.remove(num)
            log = "Fabric" + its36(num)
            pas = "".join([random.choice(chars) for _ in range(15)])
            res.append({'login': log, 'password': pas})
            obj = LoyalUser.objects.create(login=log, role='fabric', name=log)
            obj.set_password(pas)
            obj.save()
        return JsonResponse({'count': len(res), 'result': res})


class Login(View):
    def post(self, request):
        login, pas = extract_auth_data(request.body)
        if login is None:
            return HttpResponse(status=400)
        try:
            usr = LoyalUser.objects.get(login=login)
            if usr.check_password(pas):
                token = create_token(usr)
                usr.refresh_token = uuid.uuid4()
                usr.save()
                return HttpResponseRedirect(
                    "/auth/complete?auth_token=" + token.decode('utf-8') + "&refresh_token=" + usr.refresh_token.hex)
            else:
                return process_error(AuthError("wrong login/pass"))
        except ObjectDoesNotExist:
            return process_error(AuthError("wrong login/pass"))


class Refresh(View):
    def post(self, request):
        try:
            data = json.loads(request.body.decode("utf-8"))
            rt = data['refresh_token']
        except json.JSONDecodeError:
            # wrong data
            return process_error(AuthError("wrong refresh token"))
        except KeyError:
            # wrong data
            return process_error(AuthError("wrong refresh token"))

        try:
            usr = LoyalUser.objects.get(refresh_token=rt)

            token = create_token(usr)
            usr.refresh_token = uuid.uuid4()
            usr.save()
            return HttpResponseRedirect(
                "/auth/complete?auth_token=" + token.decode('utf-8') + "&refresh_token=" + usr.refresh_token.hex)

        except ObjectDoesNotExist:
            return process_error(AuthError("wrong refresh token"))


class Stub(View):
    def get(self, request):
        auth_token = request.GET.get('auth_token', None)
        if auth_token is not None:
            resp = HttpResponseRedirect('/')
            resp.set_cookie('auth_token', auth_token)
            return resp
        return HttpResponseRedirect('/')


# /auth/{mode}
auth_urls = {'vk': ("https://oauth.vk.com/authorize?"
                    "client_id={}&"
                    "display=popup&"  # если устройство мобильное, то vk сам заменит на mobile
                    "redirect_uri={}&"
                    "scope=0&"
                    "response_type=code&"
                    "v=5.62"),

             'fb': ("https://www.facebook.com/v2.8/dialog/oauth?"
                    "client_id={}&"
                    "response_type=code&"
                    "redirect_uri={}"),

             'go': ("https://accounts.google.com/o/oauth2/v2/auth?"
                    "client_id={}&"
                    "response_type=code&"
                    "scope=profile&"
                    "redirect_uri={}")
             }


class AuthSocial(View):
    def get(self, request, mode):
        mode = mode.lower()
        if mode in auth_urls.keys():
            url = auth_urls[mode]
            with open('authorization/credentials/{}.json'.format(mode)) as data_file:
                data = json.load(data_file)
            complete_url = url.format(data['client_id'], data['redirect_uris'][0])
            return HttpResponseRedirect(complete_url)
        else:
            return HttpResponseRedirect("/auth/complete?error=wrong_mode")


def _vk_callback(r, i=0):
    code = r.GET.get('code', None)
    if code is None:
        raise AuthError('no_code_returned')
    c = client.HTTPSConnection('oauth.vk.com')
    with open('authorization/credentials/vk.json') as data_file:
        data = json.load(data_file)
    c.request("GET", ("/access_token?"
                      "client_id={}&"
                      "client_secret={}&"
                      "redirect_uri={}&"
                      "code={}").format(data['client_id'], data['client_secret'], data['redirect_uris'][i], code))
    response = c.getresponse()
    if response.status != 200:
        if response.status >= 500:
            raise AuthError("unknown_error")
        else:
            raise AuthError("wrong_data")
    j = response.read().decode()
    c.close()
    client_data = json.loads(j)
    if "error" in client_data.keys():
        raise AuthError(client_data["error"])

    try:
        return {'vk_id': str(client_data["user_id"])}
    except KeyError:
        raise AuthError("provider_not_available")


def _fb_callback(r, i=0):
    code = r.GET.get('code', None)
    if code is None:
        raise AuthError('no_code_returned')
    c = client.HTTPSConnection('graph.facebook.com')
    with open('authorization/credentials/fb.json') as data_file:
        data = json.load(data_file)
    c.request("GET", ("/v2.8/oauth/access_token?"
                      "client_id={}&"
                      "client_secret={}&"
                      "redirect_uri={}"
                      "&code={}").format(data['client_id'], data['client_secret'], data['redirect_uris'][i], code))
    response = c.getresponse()
    if response.status != 200:
        print(response.read())
        if response.status >= 500:
            raise AuthError("unknown_error")
        else:
            raise AuthError("provider_not_available")
    j = response.read().decode()

    client_data = json.loads(j)
    if "error" in client_data.keys():
        raise AuthError(client_data["error"])

    c.request("GET", ("/v2.8/me?"
                      "access_token={}").format(client_data['access_token']))
    response = c.getresponse()
    if response.status != 200:
        if response.status >= 500:
            raise AuthError("unknown_error")
        else:
            raise AuthError("provider_not_available")
    j = response.read().decode()
    c.close()
    user_data = json.loads(j)

    try:
        return {'fb_id': user_data["id"]}
    except KeyError:
        raise AuthError("provider_not_available")


def _go_callback(r, i=0):
    code = r.GET.get('code', None)
    if code is None:
        raise AuthError('no_code_returned')
    c = client.HTTPSConnection('www.googleapis.com')
    with open('tetra_auth/credentials/go.json') as data_file:
        data = json.load(data_file)

    body = urllib.parse.urlencode({
        "client_id": data['client_id'],
        "client_secret": data['client_secret'],
        "redirect_uri": data['redirect_uris'][i],
        "code": code,
        "grant_type": "authorization_code"})
    c.request("POST", "/oauth2/v4/token", body, headers={'Content-Type': 'application/x-www-form-urlencoded'})

    response = c.getresponse()
    if response.status != 200:
        if response.status >= 500:
            raise AuthError("unknown_error")
        else:
            raise AuthError("provider_not_available")
    j = response.read().decode()
    c.close()
    data = json.loads(j)
    if "error" in data.keys():
        raise AuthError(data["error"])

    def base64url_decode(input):
        if isinstance(input, str):
            input = input.encode('ascii')

        rem = len(input) % 4

        if rem > 0:
            input += b'=' * (4 - rem)

        return base64.urlsafe_b64decode(input)

    t = data['id_token']
    tt = t.split('.')[1]
    payload_data = base64url_decode(tt)
    payload = json.loads(payload_data.decode('utf-8'))

    try:
        return {'go_id': payload["sub"]}
    except KeyError:
        raise AuthError("provider_not_available")


class CallbackSocial(View):
    def get(self, r, mode):
        if mode not in auth_urls.keys():
            return process_error(AuthError("wrong_mode"))
        error = r.GET.get('error', None)
        if error is None:
            try:
                userid = eval("_{}_callback(r)".format(mode))
            except AuthError as ae:
                return process_error(ae)
            except Exception as e:
                return process_error(AuthError("unknown_error"))
            try:
                user = LoyalUser.objects.get(**userid)
            except ObjectDoesNotExist:
                user = LoyalUser.objects.create(**userid)
            token = create_token(user)
            user.refresh_token = uuid.uuid4()
            user.save()
            return HttpResponseRedirect(
                "/auth/complete?auth_token=" + token.decode('utf-8') + "&refresh_token=" + user.refresh_token.hex)

        else:
            return process_error(AuthError(error))


class BindSocial(View):
    def get(self, r, mode):
        mode = mode.lower()
        if mode in auth_urls.keys():
            url = auth_urls[mode]
            with open('authorization/credentials/{}.json'.format(mode)) as data_file:
                data = json.load(data_file)
            complete_url = url.format(data['client_id'], data['redirect_uris'][1])
            return HttpResponseRedirect(complete_url)
        else:
            return HttpResponseRedirect("/auth/complete?error=wrong_mode")


class MergeSocial(View):
    def get(self, r, mode):
        auth = check_authorisation(r)
        if auth is None:
            return HttpResponse(status=401)

        if mode not in auth_urls.keys():
            return process_error(AuthError("wrong_mode"))
        error = r.GET.get('error', None)
        if error is None:
            try:
                userid = eval("_{}_callback(r, 1)".format(mode))
            except AuthError as ae:
                return process_error(ae)
            except Exception:
                return process_error(AuthError("unknown_error"))

            try:
                user = LoyalUser.objects.get(id=uuid.UUID(auth['Id']))
            except ObjectDoesNotExist:
                return process_error(AuthError("unknown_error"))
            k, v = list(userid.items())[0]
            setattr(user, k, v)
            user.save()
            return HttpResponseRedirect("/auth/complete")
        else:
            return process_error(AuthError(error))


class UsersView(View):
    def get(self, r, user):
        auth = check_authorisation(r)
        if auth is None:
            return HttpResponse(status=401)
        if not check_role(auth, ['manager']):
            return HttpResponse(status=403)
        if user is None:
            try:
                page = int(r.GET.get('page', 1))
            except ValueError:
                page = 1
            try:
                count = int(r.GET.get('count', 10))
            except ValueError:
                count = 10
            p = Paginator(LoyalUser.objects.all(), count)
            objs = p.page(page)
        else:
            o = get_object_or_404(LoyalUser, id=uuid.UUID(user))
            objs = [o]
        res = serializers.serialize('json', objs, fields=('login', 'name', 'vk_id', 'fb_id', 'go_id', 'ok_id', 'role'))
        body = '{{"count":{}, "result":{} }}'.format(str(LoyalUser.objects.count()), res)
        return HttpResponse(body, content_type='application/json')

    def post(self, r, user):
        auth = check_authorisation(r)
        if auth is None:
            return HttpResponse(status=401)
        if not check_role(auth, ['manager']):
            return HttpResponse(status=403)
        if user is None:
            try:
                data = json.loads(r.body.decode())
                keys = ['login', 'name', 'vk_id', 'fb_id', 'go_id', 'ok_id', 'role']
                iv = {k: v for k, v in data.items() if k in keys}
                obj = LoyalUser.objects.create(**iv)
                if 'password' in data:
                    obj.set_password(data['password'])
                    obj.save()
                return JsonResponse({'id': obj.pk})
            except json.JSONDecodeError:
                # wrong data
                return HttpResponse(status=400)
            except KeyError:
                # wrong data
                return HttpResponse(status=400)
        else:
            return HttpResponse(status=405)

    def patch(self, r, user):
        auth = check_authorisation(r)
        if auth is None:
            return HttpResponse(status=401)
        if user is not None:
            if not check_role(auth, ['manager']):
                return HttpResponse(status=403)
            obj = get_object_or_404(LoyalUser, id=uuid.UUID(user))
            try:
                data = json.loads(r.body.decode())
                keys = ['login', 'name', 'vk_id', 'fb_id', 'go_id', 'ok_id', 'role']
                for k in keys:
                    if k in data:
                        setattr(obj, k, data[k])
                if 'password' in data:
                    obj.set_password(data['password'])
                obj.save()
                return HttpResponse(status=200)
            except json.JSONDecodeError:
                # wrong data
                return HttpResponse(status=400)
            except KeyError:
                # wrong data
                return HttpResponse(status=400)
        else:
            if not check_role(auth, ['user', 'manager']):
                return HttpResponse(status=403)
            obj = get_object_or_404(LoyalUser, id=uuid.UUID(auth['Id']))
            try:
                data = json.loads(r.body.decode())
                keys = ['login', 'name']
                for k in keys:
                    if k in data:
                        setattr(obj, k, data[k])
                if 'password' in data:
                    obj.set_password(data['password'])
                obj.save()
                return HttpResponse(status=200)
            except json.JSONDecodeError:
                # wrong data
                return HttpResponse(status=400)
            except KeyError:
                # wrong data
                return HttpResponse(status=400)

    def delete(self, r, user):
        auth = check_authorisation(r)
        if auth is None:
            return HttpResponse(status=401)
        if not check_role(auth, ['manager']):
            return HttpResponse(status=403)
        if user is not None:
            obj = get_object_or_404(LoyalUser, id=uuid.UUID(user))
            obj.delete()
            return HttpResponse(status=206)
        else:
            return HttpResponse(status=405)
