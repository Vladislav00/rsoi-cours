import json
from http import client
from json import JSONDecodeError

from agregator.settings import BASE_DOMAIN
from home.utils import queued, get_service_token


def get_exchange_rate():
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("GET", "/exchangerate")
    rp = c.getresponse()
    if rp.status == 200:
        try:
            data = json.loads(rp.read().decode())
            er = float(data['exchangerate'])
        except JSONDecodeError:
            return None
        except KeyError:
            return None
        except ValueError:
            return None
        return er
    else:
        return None


def get_prizes(page, count):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("GET", "/prize?page={}&count={}".format(page, count))
    rp = c.getresponse()
    if rp.code != 200:
        return 0, []
    else:
        try:
            data = json.loads(rp.read().decode())
            count = data["count"]
            data = data["result"]
            for d in data:
                del d["model"]
                f = d['fields']
                for k, v in f.items():
                    d[k] = v
                del d['fields']
            return count, data
        except JSONDecodeError:
            return 0, []


def get_prize(p_id):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("GET", "/prize/{}".format(p_id))
    rp = c.getresponse()
    if rp.code != 200:
        return None
    else:
        try:
            d = json.loads(rp.read().decode())[0]
            del d["model"]
            f = d['fields']
            for k, v in f.items():
                d[k] = v
            del d['fields']
            return d
        except JSONDecodeError:
            return None


def get_my_balance(user_token):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("GET", "/balance", headers={"AUTHORIZATION": user_token['token']})
    rp = c.getresponse()
    if rp.code != 200:
        return 0
    else:
        try:
            d = json.loads(rp.read().decode())
            return d['Balance']
        except JSONDecodeError:
            return 0


class RetryException(Exception):
    pass


@queued
def add_money(user_id, reason):
    c = client.HTTPConnection(BASE_DOMAIN)
    data = json.dumps({'Id': user_id, 'add': reason})
    c.request("POST", "/balance", data, headers={"AUTHORIZATION": get_service_token()})
    rp = c.getresponse()
    if rp.code != 200:
        raise RetryException()


def withdraw_money(user_id, count, real):
    c = client.HTTPConnection(BASE_DOMAIN)
    data = json.dumps({'Id': user_id, 'withdraw': count, 'real': real})
    c.request("POST", "/balance", data, headers={"AUTHORIZATION": get_service_token()})
    rp = c.getresponse()
    if rp.code != 200:
        if rp.code == 402:
            return False
        return None
    return True


@queued
def order_prize(user_id, prize, contacts):
    c = client.HTTPConnection(BASE_DOMAIN)
    data = json.dumps({'user': user_id, 'prize': prize, 'user_contacts': contacts})
    c.request("POST", "/order", data, headers={"AUTHORIZATION": get_service_token()})
    rp = c.getresponse()
    if rp.code != 200:
        raise RetryException()


def get_preferences(manager_token):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("GET", "/economic", headers={"AUTHORIZATION": manager_token['token']})
    rp = c.getresponse()
    if rp.code != 200:
        return {}
    else:
        try:
            d = json.loads(rp.read().decode())
            return d
        except JSONDecodeError:
            return None


@queued
def set_preferences(manager_token, prefs):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("POST", "/economic", json.dumps(prefs), headers={"AUTHORIZATION": manager_token['token']})
    rp = c.getresponse()
    if rp.code != 200:
        raise RetryException()


def register_fabric(manager_token, count):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("POST", "/auth/fabric/{}".format(count), headers={"AUTHORIZATION": manager_token['token']})
    rp = c.getresponse()
    if rp.code != 200:
        return None
    else:
        try:
            return json.loads(rp.read().decode())
        except JSONDecodeError:
            return None


def delete_user(manager_token, user):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("DELETE", "/auth/user/{}".format(user), headers={"AUTHORIZATION": manager_token['token']})
    rp = c.getresponse()
    if rp.code != 206 and rp.code != 404:
        return False
    return True


def get_userlist(manager_token, page, count):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("GET", "/auth/user?page={}&count={}".format(page, count),
              headers={"AUTHORIZATION": manager_token['token']})
    rp = c.getresponse()
    if rp.code != 200:
        return 0, []
    else:
        try:
            data = json.loads(rp.read().decode())
            count = data["count"]
            data = data["result"]
            for d in data:
                del d["model"]
                f = d['fields']
                for k, v in f.items():
                    d[k] = v
                del d['fields']
            return count, data
        except JSONDecodeError:
            return 0, []


def get_user(manager_token, u_id):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("GET", "/auth/user/{}".format(u_id), headers={"AUTHORIZATION": manager_token['token']})
    rp = c.getresponse()
    if rp.code != 200:
        return None
    else:
        try:
            d = json.loads(rp.read().decode())["result"][0]
            del d["model"]
            f = d['fields']
            for k, v in f.items():
                d[k] = v
            del d['fields']
            return d
        except JSONDecodeError:
            return None


def get_user_balance(manager_token, u_id):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("GET", "/balance", json.dumps({'user': u_id}), headers={"AUTHORIZATION": manager_token['token']})
    rp = c.getresponse()
    if rp.code != 200:
        return 0
    else:
        try:
            d = json.loads(rp.read().decode())
            return d['Balance']
        except JSONDecodeError:
            return 0


def set_user_balance(manager_token, u_id, value):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("PATCH", "/balance", json.dumps({'Id': u_id, 'Balance': value}),
              headers={"AUTHORIZATION": manager_token['token']})
    rp = c.getresponse()
    return rp.code == 200


@queued
def delete_user_balance(manager_token, u_id):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("DELETE", "/balance", json.dumps({'Id': u_id}), headers={"AUTHORIZATION": manager_token['token']})
    rp = c.getresponse()
    if rp.code != 206:
        raise RetryException()


def update_user(manager_token, u_id, data):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("PATCH", "/auth/user/{}".format(u_id) if u_id else "/auth/user", json.dumps(data),
              headers={"AUTHORIZATION": manager_token['token']})
    rp = c.getresponse()
    return rp.code == 200


def create_user(manager_token, data):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("POST", "/auth/user", json.dumps(data),
              headers={"AUTHORIZATION": manager_token['token']})
    rp = c.getresponse()
    if rp.code != 200:
        return None
    else:
        try:
            d = json.loads(rp.read().decode())
            return d['id']
        except JSONDecodeError:
            return None


def delete_prize(manager_token, prize):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("DELETE", "/prize/{}".format(prize), headers={"AUTHORIZATION": manager_token['token']})
    rp = c.getresponse()
    if rp.code != 206 and rp.code != 404:
        return False
    return True


def get_prizelist(manager_token, page, count):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("GET", "/prize?page={}&count={}".format(page, count),
              headers={"AUTHORIZATION": manager_token['token']})
    rp = c.getresponse()
    if rp.code != 200:
        return 0, []
    else:
        try:
            data = json.loads(rp.read().decode())
            count = data["count"]
            data = data["result"]
            for d in data:
                del d["model"]
                f = d['fields']
                for k, v in f.items():
                    d[k] = v
                del d['fields']
            return count, data
        except JSONDecodeError:
            return 0, []


def update_prize(manager_token, u_id, body, ct):
    c = client.HTTPConnection(BASE_DOMAIN)

    c.request("PATCH", "/prize/{}".format(u_id), body,
              headers={"AUTHORIZATION": manager_token['token'], "Content-type": ct})
    rp = c.getresponse()
    return rp.code == 200


def create_prize(manager_token, body, ct):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("POST", "/prize", body,
              headers={"AUTHORIZATION": manager_token['token'], "Content-type": ct})
    rp = c.getresponse()
    if rp.code != 200:
        return None
    else:
        try:
            d = json.loads(rp.read().decode())
            return d['id']
        except JSONDecodeError:
            return None


def delete_order(manager_token, order):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("DELETE", "/order/{}".format(order), headers={"AUTHORIZATION": manager_token['token']})
    rp = c.getresponse()
    if rp.code != 206 and rp.code != 404:
        return False
    return True


def get_orderlist(token, page, count):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("GET", "/order?page={}&count={}".format(page, count),
              headers={"AUTHORIZATION": token['token']})
    rp = c.getresponse()
    if rp.code != 200:
        return 0, []
    else:
        try:
            data = json.loads(rp.read().decode())
            count = data["count"]
            data = data["result"]
            for d in data:
                del d["model"]
                f = d['fields']
                for k, v in f.items():
                    d[k] = v
                del d['fields']
            return count, data
        except JSONDecodeError:
            return 0, []


def update_order(manager_token, o_id, data):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("PATCH", "/order/{}".format(o_id), json.dumps(data),
              headers={"AUTHORIZATION": manager_token['token']})
    rp = c.getresponse()
    return rp.code == 200


def create_order(manager_token, data):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("POST", "/order", json.dumps(data),
              headers={"AUTHORIZATION": manager_token['token']})
    rp = c.getresponse()
    if rp.code != 200:
        return None
    else:
        try:
            d = json.loads(rp.read().decode())
            return d['id']
        except JSONDecodeError:
            return None


def get_order(token, o_id):
    c = client.HTTPConnection(BASE_DOMAIN)
    c.request("GET", "/order/{}".format(o_id), headers={"AUTHORIZATION": token['token']})
    rp = c.getresponse()
    if rp.code != 200:
        return None
    else:
        try:
            d = json.loads(rp.read().decode())[0]
            del d["model"]
            f = d['fields']
            for k, v in f.items():
                d[k] = v
            del d['fields']
            return d
        except JSONDecodeError:
            return None