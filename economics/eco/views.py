import datetime
import json
import math

import redis
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import JsonResponse
from django.views import View

from eco.utils import check_authorisation, check_role

redis_host = 'localhost'
redis_port = 6379
redis_db = 6


def stf(value, default=None):
    try:
        return float(value)
    except ValueError:
        return default
    except TypeError:
        return default


def sti(value, default=None):
    try:
        return int(value)
    except ValueError:
        return default
    except TypeError:
        return default


def dec(binval):
    if binval is None:
        return None
    else:
        return binval.decode()


def exchange_rate(request: HttpRequest):
    r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
    Coeff = r.get('Exchange_rate')
    if Coeff is None:
        Today = datetime.datetime.utcnow().timestamp()
        Start_date = stf(r.get('Start_date'), Today - datetime.timedelta(days=1).total_seconds())
        End_date = stf(r.get('End_date'), Today + datetime.timedelta(days=1).total_seconds())
        Start_money = sti(r.get('Start_money'), 1)
        Current_money = sti(r.get('Current_money'), 0)
        Base_course = stf(r.get('Base_course'), 1)

        Expectation_money = Start_money * (End_date - Today) / (End_date - Start_date)
        Coeff = Base_course * math.exp((Expectation_money - Current_money) / Start_money)
        rt = sti(r.get('Refresh_time'), 60)
        r.set('Exchange_rate', Coeff, rt)
    else:
        Coeff = Coeff.decode()
    return JsonResponse({'exchangerate': Coeff})


def economic(request: HttpRequest):
    params = ['Start_date', 'End_date', 'Start_money', 'Current_money', 'Base_course', 'Refresh_time', 'Code_bonus']
    auth = check_authorisation(request)
    if auth is None:
        return HttpResponse(status=401)
    if not check_role(auth, ['manager']):
        return HttpResponse(status=403)
    r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
    if request.method == 'GET':
        return JsonResponse({k: dec(r.get(k)) for k in params})
    else:
        try:
            data = json.loads(request.body.decode())
            for k in params:
                if k in data and data[k] is not None:
                    r.set(k, data[k])
            r.delete('Exchange_rate')
            r.save()
            return HttpResponse(status=200)
        except json.JSONDecodeError:
            # wrong data
            return HttpResponse(status=400)


class BalanceView(View):
    def get(self, request: HttpRequest):
        auth = check_authorisation(request)
        if auth is None:
            return HttpResponse(status=401)
        if check_role(auth, ['manager']):  # for user
            try:
                user = json.loads(request.body.decode())['user'].replace('-', '')
                r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
                b = r.get("usr_{}".format(user))
                return JsonResponse({'Balance': int(b.decode()) if b else 0})
            except json.JSONDecodeError:
                # wrong data
                return HttpResponse(status=400)
            except KeyError:
                # wrong data
                return HttpResponse(status=400)

        elif check_role(auth, ['user']):  # my
            r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
            b = r.get("usr_{}".format(auth['Id']))
            return JsonResponse({'Balance': int(b.decode()) if b else 0})
        else:
            return HttpResponse(status=403)

    def post(self, request: HttpRequest):
        auth = check_authorisation(request)
        if auth is None:
            return HttpResponse(status=401)
        if not check_role(auth, ['service']):
            return HttpResponse(status=403)
        r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
        try:
            data = json.loads(request.body.decode())
            print(data)
            user = "usr_{}".format(data['Id'])
            if "withdraw" in data and "real" in data:
                ob = sti(r.get(user), 0)
                wd = abs(sti(data['withdraw'], 0))
                rc = abs(sti(data['real'], 0))
                if wd > ob:
                    return HttpResponse(json.dumps({'Error': "Balance too low"}), status=402,
                                        content_type='application/json')
                Current_money = sti(r.get('Current_money'), 0)
                r.set('Current_money', Current_money - rc)
                r.set(user, ob - wd)
                return HttpResponse(status=200)
            elif "add" in data:
                reason = data['add']
                if reason == 'code':
                    a = sti(r.get('Code_bonus'), 10)
                    ob = sti(r.get(user), 0)
                    r.set(user, ob + a)
                    return HttpResponse(status=200)
            return HttpResponse(status=400)
        except json.JSONDecodeError:
            # wrong data
            return HttpResponse(status=400)
        except KeyError:
            # wrong data
            return HttpResponse(status=400)

    def patch(self, request: HttpRequest):
        auth = check_authorisation(request)
        if auth is None:
            return HttpResponse(status=401)
        if not check_role(auth, ['manager']):
            return HttpResponse(status=403)
        try:
            data = json.loads(request.body.decode())
            user = "usr_{}".format(data['Id'].replace('-', ''))
            balance = data['Balance']
            r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
            r.set(user, balance)
            return HttpResponse(status=200)
        except json.JSONDecodeError:
            # wrong data
            return HttpResponse(status=400)
        except KeyError:
            # wrong data
            return HttpResponse(status=400)

    def delete(self, request: HttpRequest):
        auth = check_authorisation(request)
        if auth is None:
            return HttpResponse(status=401)
        if not check_role(auth, ['manager']):
            return HttpResponse(status=403)
        try:
            data = json.loads(request.body.decode())
            user = "usr_{}".format(data['Id'].replace('-', ''))
            r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
            r.delete(user)
            return HttpResponse(status=200)
        except json.JSONDecodeError:
            # wrong data
            return HttpResponse(status=400)
        except KeyError:
            # wrong data
            return HttpResponse(status=400)
