import json

from django.http import HttpResponse
from django.http import JsonResponse
from django.views import View
import redis

from codes.utils import check_authorisation, check_role

redis_host = 'localhost'
redis_port = 6379
redis_db = 5


class BonusView(View):
    def get(self, request, code=None):
        auth = check_authorisation(request)
        if auth is None:
            return HttpResponse(status=401)

        if code is None:  # code list, manager auth
            if not check_role(auth, ['manager']):
                return HttpResponse(status=403)
            try:
                page = int(request.GET.get('page', 1))
            except ValueError:
                page = 1
            try:
                count = int(request.GET.get('count', 10))
            except ValueError:
                count = 10
            r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
            res = []
            it = 0
            for i in range(page):
                it, res = r.scan(it, count=count)
                if it == 0:
                    if i != page-1:
                        res = []
                    break
            return JsonResponse([a.decode('ascii') for a in res], safe=False)

        else:  # get code state, service auth
            if not check_role(auth, ['service']):
                return HttpResponse(status=403)
            r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
            stat = r.get(code)
            if stat is not None:
                return JsonResponse({'status': stat})
        return HttpResponse(status=500)

    def post(self, request, code=None):
        auth = check_authorisation(request)
        if auth is None:
            return HttpResponse(status=401)

        if code is None:  # upload code list, fabric or manager auth
            if not check_role(auth, ['fabric', 'manager']):
                return HttpResponse(status=403)
            try:
                codes = json.loads(request.body.decode("utf-8"))  # array of codes
            except json.JSONDecodeError:
                # wrong data
                return HttpResponse(status=400)
            r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
            pipe = r.pipeline()
            for code in codes:
                pipe.set(code, 'new')
            pipe.execute()
            r.save()
            return HttpResponse(status=200)

        else:  # redeem code , service auth
            if not check_role(auth, ['service']):
                return HttpResponse(status=403)
            try:
                user = json.loads(request.body.decode("utf-8"))['user']
            except json.JSONDecodeError:
                # wrong data
                return HttpResponse(status=400)
            except KeyError:
                # wrong data
                return HttpResponse(status=400)
            r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
            status = r.get(code).decode()
            if status == 'new':
                r.set(code, 'taken'+str(user))
                return HttpResponse(status=200)
            else:
                return HttpResponse(status=410)

    def patch(self, request, code=None):
        if code is None:
            # not available
            return HttpResponse(status=405)
        else:
            # change code state, manager auth
            auth = check_authorisation(request)
            if auth is None:
                return HttpResponse(status=401)
            if not check_role(auth, ['manager']):
                return HttpResponse(status=403)
            try:
                status = json.loads(request.body.decode("utf-8"))['status']
            except json.JSONDecodeError:
                # wrong data
                return HttpResponse(status=400)
            except KeyError:
                # wrong data
                return HttpResponse(status=400)
            r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
            r.set(code, status)
            return HttpResponse(status=200)

    def delete(self, request, code=None):
        if code is None:
            # not available
            return HttpResponse(status=405)
        else:
            # delete code, manager auth
            auth = check_authorisation(request)
            if auth is None:
                return HttpResponse(status=401)
            if not check_role(auth, ['manager']):
                return HttpResponse(status=403)
            r = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)
            r.delete(code)
            return HttpResponse(status=204)
