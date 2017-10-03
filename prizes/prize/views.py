import json
import uuid

from django.core.paginator import Paginator
from django.core import serializers
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from prize.models import Prize, Order
from prize.utils import check_authorisation, check_role
from prize.forms import PrizeForm


class PrizeView(View):
    def get(self, r, prize=None):
        if prize is None:  # return list on prizes
            try:
                page = int(r.GET.get('page', 1))
            except ValueError:
                page = 1
            try:
                count = int(r.GET.get('count', 1))
            except ValueError:
                count = 10
            p = Paginator(Prize.objects.order_by('cost').all(), count)
            pg = p.page(page)
            objs = pg.object_list
            res = serializers.serialize('json', objs)
            body = '{{"count":{}, "result":{} }}'.format(str(Prize.objects.count()), res)
            return HttpResponse(body, content_type='application/json')
        else:  # return prize
            pr = get_object_or_404(Prize, id=uuid.UUID(prize))
            return HttpResponse(serializers.serialize('json', [pr]), content_type='application/json')

    def post(self, r, prize=None):
        if prize is None:  # add prize. manager access
            auth = check_authorisation(r)
            if auth is None:
                return HttpResponse(status=401)
            if not check_role(auth, ['manager']):
                return HttpResponse(status=403)
            form = PrizeForm(r.POST, r.FILES)
            if form.is_valid():
                obj = Prize.objects.create(title=form.cleaned_data['title'],
                                     pic=form.cleaned_data['pic'],
                                     cost=form.cleaned_data['cost'],
                                     provider=form.cleaned_data['provider'])
                return JsonResponse({'id': obj.id})
            else:
                return HttpResponse(status=400)
        else:  # not available
            return HttpResponse(status=405)

    def patch(self, r, prize=None):
        r.method ='POST'
        if prize is not None:  # edit prize. manager access
            auth = check_authorisation(r)
            if auth is None:
                return HttpResponse(status=401)
            if not check_role(auth, ['manager']):
                return HttpResponse(status=403)
            form = PrizeForm(r.POST, r.FILES)
            if form.is_valid():
                pr = get_object_or_404(Prize, id=uuid.UUID(prize))
                pr.title = form.cleaned_data['title']
                pr.pic = form.cleaned_data['pic']
                pr.cost = form.cleaned_data['cost']
                pr.provider = form.cleaned_data['provider']
                pr.save()
                return HttpResponse(status=200)
            else:
                return HttpResponse(status=400)
        else:  # not available
            return HttpResponse(status=405)

    def delete(self, r, prize=None):
        if prize is not None:  # delete prize. manager access
            auth = check_authorisation(r)
            if auth is None:
                return HttpResponse(status=401)
            if not check_role(auth, ['manager']):
                return HttpResponse(status=403)
            pr = get_object_or_404(Prize, id=uuid.UUID(prize))
            pr.delete()
            return HttpResponse(status=206)
        else:
            return HttpResponse(status=405)


class OrderView(View):
    def get(self, r, order=None):
        auth = check_authorisation(r)
        if auth is None:
            return HttpResponse(status=401)
        if order is None:  # get list of orders (my or all)
            if check_role(auth, ['manager']):  # all
                o = Order.objects.all()
            elif check_role(auth, ['user']):  # my
                o = Order.objects.filter(user=uuid.UUID(auth['Id'])).all()
            else:
                return HttpResponse(status=403)

            try:
                page = int(r.GET.get('page', 1))
            except ValueError:
                page = 1
            try:
                count = int(r.GET.get('count', 1))
            except ValueError:
                count = 10
            p = Paginator(o, count)
            pg = p.page(page)
            objs = pg.object_list
            res = serializers.serialize('json', objs)
            body = '{{"count":{}, "result":{} }}'.format(str(Prize.objects.count()), res)
            return HttpResponse(body, content_type='application/json')
        else:  # get order (my or any)
            if check_role(auth, ['manager']):  # any
                o = get_object_or_404(Order, id=order)
            elif check_role(auth, ['user']):  # my
                o = get_object_or_404(Order, id=order, user=uuid.UUID(auth['Id']))
            else:
                return HttpResponse(status=403)
            return HttpResponse(serializers.serialize('json', [o]), content_type='application/json')

    def post(self, r, order=None):
        if order is not None:
            # not available
            return HttpResponse(status=405)
        auth = check_authorisation(r)
        if auth is None:
            return HttpResponse(status=401)
        if not check_role(auth, ['service', 'manager']):
            return HttpResponse(status=403)
        try:
            data = json.loads(r.body.decode())
            user = data['user']
            prize = data['prize']
            contacts = data['user_contacts']
            obj = Order.objects.create(prize=uuid.UUID(prize), user=uuid.UUID(user), user_contacts=contacts)
            return JsonResponse({'id': obj.id})
        except json.JSONDecodeError:
            # wrong data
            return HttpResponse(status=400)
        except KeyError:
            # wrong data
            return HttpResponse(status=400)

    def patch(self, r, order=None):
        if order is None:
            # not available
            return HttpResponse(status=405)
        auth = check_authorisation(r)
        if auth is None:
            return HttpResponse(status=401)
        if not check_role(auth, ['service']):
            return HttpResponse(status=403)
        try:
            data = json.loads(r.body.decode())
            user = data['user']
            prize = data['prize']
            contacts = data['contacts']
            o = get_object_or_404(Order, id=uuid.UUID(order))
            o.user = uuid.UUID(user)
            o.prize = uuid.UUID(prize)
            o.user_contacts = contacts
            return HttpResponse(status=200)
        except json.JSONDecodeError:
            # wrong data
            return HttpResponse(status=400)
        except KeyError:
            # wrong data
            return HttpResponse(status=400)

    def delete(self, r, order=None):
        if order is not None:  # delete prize. manager access
            auth = check_authorisation(r)
            if auth is None:
                return HttpResponse(status=401)
            if not check_role(auth, ['manager']):
                return HttpResponse(status=403)
            pr = get_object_or_404(Order, id=uuid.UUID(order))
            pr.delete()
            return HttpResponse(status=206)
        else:
            return HttpResponse(status=405)