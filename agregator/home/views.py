import datetime
import json
from http import client
from urllib.parse import urlparse, parse_qs

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views import View

from agregator.settings import BASE_DOMAIN
from home.forms import RedeemForm, LoginForm, RegisterForm, OrderForm, PreferencesForm, FabricForm, DeleteForm, \
    UserForm, \
    PrizeForm, AOrderForm, UserUpdateForm
from home.service_requests import get_exchange_rate, get_prizes, get_prize, get_my_balance, add_money, withdraw_money, \
    order_prize, get_preferences, set_preferences, register_fabric, delete_user, get_userlist, get_user, \
    get_user_balance, update_user, create_user, set_user_balance, delete_prize, get_prizelist, create_prize, \
    update_prize, get_orderlist, create_order, update_order, get_order, delete_order, delete_user_balance
from home.utils import get_service_token, check_authorisation, MyPaginator, check_role


def me_view(r: WSGIRequest):
    auth = check_authorisation(r)
    if auth is None:
        return HttpResponseRedirect("/sign")
    ctx = {'usr': auth}
    if r.method == 'POST':
        f = UserUpdateForm(r.POST)
        if f.is_valid():  # update data
            update_user(auth, None, {k: v for k, v in f.cleaned_data.items() if v != ''})
            return HttpResponseRedirect("/me")

    b = get_my_balance(auth)
    f = UserUpdateForm(initial={'name': auth['Username']})
    ctx.update({'balance': b, 'form': f})
    return render_to_response('me.html', ctx)


def me_orders_view(r):
    auth = check_authorisation(r)
    if auth is None:
        return HttpResponseRedirect("/sign")
    ctx = {'usr': auth}
    try:
        page = int(r.GET.get('page', 1))
    except ValueError:
        page = 1
    try:
        count = int(r.GET.get('count', 10))
    except ValueError:
        count = 10
    c, orders = get_orderlist(auth, page, count)
    orders = set([o['prize'] for o in orders if o is not None])
    prizes = {o: get_prize(o) for o in orders}
    obj = [p['title'] if p is not None else 'Данные о призе временно недоступны' for p in [prizes[o] for o in orders]]
    p = MyPaginator(page, count, c)
    ctx.update({'objects': obj, 'p': p})
    return render_to_response('orderlist.html', ctx)


def redeem_view(r):
    auth = check_authorisation(r)
    if auth is None:
        return HttpResponseRedirect("/sign")
    ctx = {'usr': auth}
    if r.method == 'POST':
        f = RedeemForm(r.POST)
        if f.is_valid():
            # try activate
            code = f.cleaned_data['code']
            url = "/code/{}".format(code)
            token = get_service_token()
            c = client.HTTPConnection(BASE_DOMAIN)
            c.request("POST", url, body=json.dumps({'user': auth['Id']}), headers={'Authorization': token})
            r = c.getresponse()
            if r.code != 200:
                if r.code == 410:
                    f.add_error("code", "Код уже активирован")
                else:
                    f.add_error("code", "Неизвестная ошибка")
                ctx['form'] = f
            else:
                ctx['success'] = True
                ctx['form'] = RedeemForm()
                add_money.enqueue(auth['Id'], 'code')
    else:
        f = RedeemForm()
        ctx['form'] = f
    return render_to_response('redeem.html', ctx)


def sign_view(r, action=None):
    auth = check_authorisation(r)
    if auth is not None:
        resp = HttpResponseRedirect('/sign')
        resp.delete_cookie('auth_token')
        return resp
    if r.method == 'POST':
        if action == 'auth':
            lf = LoginForm(r.POST)
            if lf.is_valid():
                ac = {'login': lf.cleaned_data['login'], 'password': lf.cleaned_data['pas']}
                c = client.HTTPConnection(BASE_DOMAIN)
                c.request("POST", "/auth/login", body=json.dumps(ac))
                rp = c.getresponse()
                if rp.code == 302:
                    loc = rp.getheader('location')
                    o = urlparse(loc)
                    qs = parse_qs(o.query)
                    if 'error' in qs:
                        err = qs['error']
                        if err == ['wrong_login/pass']:
                            lf.add_error("__all__", "Неверный логин или пароль")
                        rf = RegisterForm()
                    else:
                        return HttpResponseRedirect(loc)
                else:
                    lf.add_error("__all__", "Произошла неизвестная ошибка, повторите попытку позже")
                    rf = RegisterForm()
            else:
                rf = RegisterForm()
            ctx = {'lform': lf, 'rform': rf}
        else:
            rf = RegisterForm(r.POST)
            if rf.is_valid():
                if rf.cleaned_data['pas'] == rf.cleaned_data['pas_again']:
                    ac = {'login': rf.cleaned_data['login'], 'password': rf.cleaned_data['pas']}
                    c = client.HTTPConnection(BASE_DOMAIN)
                    c.request("POST", "/auth/register", body=json.dumps(ac))
                    rp = c.getresponse()
                    if rp.code == 302:
                        loc = rp.getheader('location')
                        o = urlparse(loc)
                        qs = parse_qs(o.query)
                        if 'error' in qs:
                            err = qs['error']
                            if 'login_already_in_use' in err:
                                rf.add_error("login", "Данное имя уже занято")
                            if 'password_too_short' in err:
                                rf.add_error("pas", "Пароль слишком короткий")
                            lf = LoginForm()
                            ctx = {'lform': lf, 'rform': rf}
                        else:
                            return HttpResponseRedirect(loc)
                    elif rp.code == 200:
                        lf = LoginForm()
                        rf = RegisterForm()
                        ctx = {'lform': lf, 'rform': rf, 'success': True}

                    else:
                        rf.add_error("__all__", "Произошла неизвестная ошибка, повторите попытку позже")
                        lf = RegisterForm()
                        ctx = {'lform': lf, 'rform': rf}
                else:
                    rf.add_error("pas_again", "Пароли не совпадают")
                    lf = LoginForm()
                    ctx = {'lform': lf, 'rform': rf}
            else:
                lf = LoginForm()
                ctx = {'lform': lf, 'rform': rf}

    else:
        lf = LoginForm()
        rf = RegisterForm()
        ctx = {'lform': lf, 'rform': rf}
    return render_to_response('sign.html', ctx)


class ShopView(View):
    def get(self, r: HttpRequest, prize=None):

        er = get_exchange_rate()
        if er is None:
            def cost(x):
                return None
        else:
            def cost(x):
                return int(x * er)

        auth = check_authorisation(r)
        ctx = {'usr': auth}
        if auth is not None:
            if not check_role(auth, ['user']):
                return HttpResponseRedirect('/admin')
        if prize is None or prize == 'available':  # list
            try:
                page = int(r.GET.get('page', 1))
            except ValueError:
                page = 1
            try:
                count = int(r.GET.get('count', 10))
            except ValueError:
                count = 10
            if auth is not None:
                balance = get_my_balance(auth)
            else:
                balance = None
            c, obj = get_prizes(page, count)
            for o in obj:
                o['cost'] = cost(o['cost'])
            if prize == 'available':
                if auth is None:
                    return HttpResponseRedirect("\shop")
                else:
                    # available only
                    def cmp(a, b):
                        if a is None or b is None:
                            return False
                        else:
                            return a <= b

                    nobj = [o for o in obj if cmp(o['cost'], balance)]
                    if len(nobj) != len(obj):
                        c = count * (page - 1) + len(nobj)
                    else:
                        c = count * page + 1  # no way to know real count
                    obj = nobj

            p = MyPaginator(page, count, c)

            queries_without_page = r.GET.copy()
            if 'page' in queries_without_page:
                del queries_without_page['page']
            ctx.update({'objects': obj, 'p': p, 'queries': queries_without_page, 'balance': balance,
                        'success': r.GET.get('success', None)})
            return render_to_response('shop.html', ctx)
        else:  # single prize and order
            auth = check_authorisation(r)
            p = get_prize(prize)
            if p is None:
                # not available
                return render_to_response('prize.html', ctx)
            f = OrderForm()
            er = get_exchange_rate()
            if er is None:
                def cost(x):
                    return None
            else:
                def cost(x):
                    return int(x * er)
            p['cost'] = cost(p['cost'])
            if auth is not None and er is not None:
                balance = get_my_balance(auth)
                can_order = float(balance) >= float(p['cost']) if p['cost'] is not None else False
            else:
                can_order = False
            ctx.update({'prize': p, 'form': f, 'can_order': can_order,
                        'success': r.GET.get('success', None)})
            return render_to_response('prize.html', ctx)

    def post(self, r: HttpRequest, prize=None):
        auth = check_authorisation(r)
        if auth is None:
            return HttpResponseRedirect('/shop')
        if prize is None or prize == 'available':
            return HttpResponseRedirect('/shop')

        ctx = {'usr': auth}
        f = OrderForm(r.POST)
        p = get_prize(prize)
        er = get_exchange_rate()
        oc = p['cost']
        if er is None:
            p['cost'] = None
        else:
            p['cost'] = int(p['cost'] * er)
        if f.is_valid():
            # try order
            if p is None or er is None:
                f.add_error('__all__', "В данный момент заказать не получилось. Повторите попытку позже.")
                ctx.update({'prize': p, 'form': f, 'can_order': True})
            status = withdraw_money(auth['Id'], p['cost'], oc)
            if status is None:
                # retry later
                f.add_error('__all__', "В данный момент заказать не получилось. Повторите попытку позже.")
                ctx.update({'prize': p, 'form': f, 'can_order': True})
            elif status:
                # queue order
                order_prize.enqueue(auth['Id'], prize,
                                    ";".join(
                                        [f.cleaned_data['name'], f.cleaned_data['phone'], f.cleaned_data['address']]))
                return HttpResponseRedirect(r.path + "?success=1")
            else:
                # need money
                f.add_error('__all__', "Недостаточно бонусов для заказа.")
                ctx.update({'prize': p, 'form': f, 'can_order': True})

        else:
            ctx.update({'prize': p, 'form': f, 'can_order': True})
        return render_to_response('prize.html', ctx)


def admin_home(r: HttpRequest):
    auth = check_authorisation(r)
    if auth is None:
        return HttpResponseRedirect('/')
    if not check_role(auth, ['manager']):
        return HttpResponseRedirect('/')
    ctx = {'usr': auth}
    return render_to_response('admin.html', ctx)


def admin_prefs(r: HttpRequest):
    auth = check_authorisation(r)
    if auth is None:
        return HttpResponseRedirect('/')
    if not check_role(auth, ['manager']):
        return HttpResponseRedirect('/')
    ctx = {'usr': auth}
    if r.method == "GET":
        pass
        # get prefs
        prefs = get_preferences(auth)
        for k in ['Start_date', 'End_date']:
            if k in prefs and prefs[k] is not None:
                prefs[k] = datetime.datetime.fromtimestamp(float(prefs[k]))
        # init form
        f = PreferencesForm(prefs)
        # show form
        ctx['form'] = f
    else:
        # parse form
        f = PreferencesForm(r.POST)
        if f.is_valid():
            # select checked

            res = {}
            for k, v in f.cleaned_data.items():
                if v and k.find("change") > 0:
                    k1 = k.rsplit('_', 1)[0]
                    res[k1] = f.cleaned_data[k1]
            for k in ['Start_date', 'End_date']:
                if k in res:
                    res[k] = res[k].timestamp()

            # send
            set_preferences.enqueue(auth, res)
            return HttpResponseRedirect('/admin')
        else:
            ctx['form'] = f
    return render_to_response('adminform.html', ctx)


def admin_fabric(r: HttpRequest):
    auth = check_authorisation(r)
    if auth is None:
        return HttpResponseRedirect('/')
    if not check_role(auth, ['manager']):
        return HttpResponseRedirect('/')
    ctx = {'usr': auth}
    if r.method == "GET":
        f = FabricForm()
    else:
        f = FabricForm(r.POST)
        if f.is_valid():
            reg = register_fabric(auth, f.cleaned_data['count'])
            if reg is None:
                f.add_error('__all__', 'Произошла ошибка. Повторите попытку позже')
            else:
                if f.cleaned_data['count'] != reg['count']:
                    f.add_error('__all__', 'Невозможно зарегестрировать больше заводов')
                ctx['obj'] = reg['result']
    ctx['form'] = f
    return render_to_response('adminformfabric.html', ctx)


def admin_user(r: HttpRequest, user=None, delete=None, create=None):
    auth = check_authorisation(r)
    if auth is None:
        return HttpResponseRedirect('/')
    if not check_role(auth, ['manager']):
        return HttpResponseRedirect('/')
    ctx = {'usr': auth}
    if delete is not None:
        if user is not None:
            if r.method == 'POST':
                # delete
                if not delete_user(auth, user):
                    df = DeleteForm()
                    df.is_valid()
                    df.add_error('__all__', 'Не удалось удалить пользователя. Повторите попытку позже.')
                    f = UserForm(r.POST)
                    ctx.update({'form': f, 'delform': df})
                    return render_to_response('adminformuniversal.html', ctx)
                else:
                    delete_user_balance.enqueue(auth, user)
        return HttpResponseRedirect('/admin/user')
    else:
        if r.method == 'GET':
            if user is None:
                if create is None:
                    # list
                    try:
                        page = int(r.GET.get('page', 1))
                    except ValueError:
                        page = 1
                    try:
                        count = int(r.GET.get('count', 10))
                    except ValueError:
                        count = 10
                    c, obj = get_userlist(auth, page, count)
                    p = MyPaginator(page, count, c)
                    obj = [{'txt': o['login'] + "-" + o['name'], 'url': '/admin/user/' + o['pk']} for o in obj]
                    queries_without_page = r.GET.copy()
                    if 'page' in queries_without_page:
                        del queries_without_page['page']
                    ctx.update({'objects': obj, 'p': p, 'queries': queries_without_page, 'r': r})
                    return render_to_response('adminitemlist.html', ctx)
                else:
                    # new form
                    f = UserForm()
                    ctx.update({'form': f, 'r': r})
                    return render_to_response('adminformuniversal.html', ctx)
            else:  # edit form
                usr = get_user(auth, user)
                if usr is not None:
                    b = get_user_balance(auth, usr['pk'])
                    if b is not None:
                        usr['balance'] = b
                    f = UserForm(initial=usr)
                else:
                    f = UserForm()
                    f.is_valid()
                    f.add_error('__all__', 'Не удалось загрузить данные, повторите попытку позже.')
                df = DeleteForm()
                ctx.update({'form': f, 'delform': df, 'r': r})
                return render_to_response('adminformuniversal.html', ctx)
        else:
            f = UserForm(r.POST)
            if f.is_valid():
                b = f.cleaned_data['balance']
                del f.cleaned_data['balance']
                d = {k: v for k, v in f.cleaned_data.items() if v != ''}

                # send
                if user is None:
                    # create
                    pk = create_user(auth, d)
                    if pk is None:
                        f.add_error('__all__', 'Не удалось загрузить данные, повторите попытку позже.')
                    else:
                        set_user_balance(auth, pk, b)
                        return HttpResponseRedirect('/admin/user/{}'.format(pk))
                else:
                    # modify
                    if not update_user(auth, user, d):
                        f.add_error('__all__', 'Не удалось обновить данные, повторите попытку позже.')
                    else:
                        if not set_user_balance(auth, user, b):
                            f.add_error('balance', 'Не удалось обновить данные, повторите попытку позже.')

            df = DeleteForm()
            ctx.update({'form': f, 'delform': df, 'r': r})
            return render_to_response('adminformuniversal.html', ctx)


def admin_prize(r: WSGIRequest, prize=None, delete=None, create=None):
    auth = check_authorisation(r)
    if auth is None:
        return HttpResponseRedirect('/')
    if not check_role(auth, ['manager']):
        return HttpResponseRedirect('/')
    ctx = {'usr': auth}
    if delete is not None:
        if prize is not None:
            if r.method == 'POST':
                # delete
                if not delete_prize(auth, prize):
                    df = DeleteForm()
                    df.is_valid()
                    df.add_error('__all__', 'Не удалось удалить приз. Повторите попытку позже.')
                    f = PrizeForm(r.POST, r.FILES)
                    ctx.update({'form': f, 'delform': df})
                    return render_to_response('adminformuniversal.html', ctx)
        return HttpResponseRedirect('/admin/prize')
    else:
        if r.method == 'GET':
            if prize is None:
                if create is None:
                    # list
                    try:
                        page = int(r.GET.get('page', 1))
                    except ValueError:
                        page = 1
                    try:
                        count = int(r.GET.get('count', 10))
                    except ValueError:
                        count = 10
                    c, obj = get_prizelist(auth, page, count)
                    p = MyPaginator(page, count, c)
                    obj = [{'txt': o['title'], 'url': '/admin/prize/' + o['pk']} for o in obj]
                    queries_without_page = r.GET.copy()
                    if 'page' in queries_without_page:
                        del queries_without_page['page']
                    ctx.update({'objects': obj, 'p': p, 'queries': queries_without_page, 'r': r})
                    return render_to_response('adminitemlist.html', ctx)
                else:
                    # new form
                    f = PrizeForm()
                    ctx.update({'form': f, 'r': r})
                    return render_to_response('adminformuniversal.html', ctx)
            else:  # edit form
                prz = get_prize(prize)
                if prz is not None:
                    f = PrizeForm(initial=prz)
                else:
                    f = PrizeForm()
                    f.is_valid()
                    f.add_error('__all__', 'Не удалось загрузить данные, повторите попытку позже.')
                df = DeleteForm()
                ctx.update({'form': f, 'delform': df, 'r': r})
                return render_to_response('adminformuniversal.html', ctx)
        else:
            # send
            if prize is None:
                # create
                pk = create_prize(auth, r.body, r.META['CONTENT_TYPE'])
                if pk is None:
                    f = PrizeForm(r.POST, r.FILES)
                    f.is_valid()
                    f.add_error('__all__', 'Не удалось загрузить данные, повторите попытку позже.')
                else:
                    return HttpResponseRedirect('/admin/prize/{}'.format(pk))
            else:
                # modify
                if not update_prize(auth, prize, r.body, r.META['CONTENT_TYPE']):
                    f = PrizeForm(r.POST, r.FILES)
                    f.is_valid()
                    f.add_error('__all__', 'Не удалось обновить данные, повторите попытку позже.')
            f = PrizeForm(r.POST, r.FILES)
            df = DeleteForm()
            ctx.update({'form': f, 'delform': df, 'r': r})
            return render_to_response('adminformuniversal.html', ctx)


def admin_order(r: WSGIRequest, order=None, delete=None, create=None):
    auth = check_authorisation(r)
    if auth is None:
        return HttpResponseRedirect('/')
    if not check_role(auth, ['manager']):
        return HttpResponseRedirect('/')
    ctx = {'usr': auth}
    if delete is not None:
        if order is not None:
            if r.method == 'POST':
                # delete
                if not delete_order(auth, order):
                    df = DeleteForm()
                    df.is_valid()
                    df.add_error('__all__', 'Не удалось удалить заказ. Повторите попытку позже.')
                    f = AOrderForm(r.POST)
                    ctx.update({'form': f, 'delform': df})
                    return render_to_response('adminformuniversal.html', ctx)
        return HttpResponseRedirect('/admin/order')
    else:
        if r.method == 'GET':
            if order is None:
                if create is None:
                    # list
                    try:
                        page = int(r.GET.get('page', 1))
                    except ValueError:
                        page = 1
                    try:
                        count = int(r.GET.get('count', 10))
                    except ValueError:
                        count = 10
                    c, obj = get_orderlist(auth, page, count)
                    p = MyPaginator(page, count, c)
                    obj = [{'txt': o['user'], 'url': '/admin/order/' + o['pk']} for o in obj]
                    queries_without_page = r.GET.copy()
                    if 'page' in queries_without_page:
                        del queries_without_page['page']
                    ctx.update({'objects': obj, 'p': p, 'queries': queries_without_page, 'r': r})
                    return render_to_response('adminitemlist.html', ctx)

                else:
                    # new form
                    f = AOrderForm()
                    ctx.update({'form': f, 'r': r})
                    return render_to_response('adminformuniversal.html', ctx)
            else:  # edit form
                ordr = get_order(auth, order)
                if ordr is not None:
                    f = AOrderForm(initial=ordr)
                else:
                    f = AOrderForm()
                    f.is_valid()
                    f.add_error('__all__', 'Не удалось загрузить данные, повторите попытку позже.')
                df = DeleteForm()
                ctx.update({'form': f, 'delform': df, 'r': r})
                return render_to_response('adminformuniversal.html', ctx)
        else:
            f = AOrderForm(r.POST)
            if f.is_valid():

                d = {k: str(v) for k, v in f.cleaned_data.items() if v != ''}

                # send
                if order is None:
                    # create
                    pk = create_order(auth, d)
                    if pk is None:
                        f.add_error('__all__', 'Не удалось загрузить данные, повторите попытку позже.')
                    else:
                        return HttpResponseRedirect('/admin/order/{}'.format(pk))
                else:
                    # modify
                    if not update_order(auth, order, d):
                        f.add_error('__all__', 'Не удалось обновить данные, повторите попытку позже.')

            df = DeleteForm()
            ctx.update({'form': f, 'delform': df, 'r': r})
            return render_to_response('adminformuniversal.html', ctx)
