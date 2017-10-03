from django.conf.urls import url

from authorization.views import Register, Login, AuthSocial, Stub, BindSocial, CallbackSocial, MergeSocial, \
    RegisterFabric, UsersView, Refresh

urlpatterns = [
    url(r'^auth/register', Register.as_view()),
    url(r'^auth/login', Login.as_view()),
    url(r'^auth/refresh', Refresh.as_view()),
    url(r'^auth/complete', Stub.as_view()),
    url(r'^auth/bind/(?P<mode>[a-z][a-z])', BindSocial.as_view()),
    url(r'^auth/callback/(?P<mode>[a-z][a-z])', CallbackSocial.as_view()),
    url(r'^auth/merge/(?P<mode>[a-z][a-z])', MergeSocial.as_view()),
    url(r'^auth/fabric/(?P<count>[0-9]*)', RegisterFabric.as_view()),
    url(r'^auth/user(/(?P<user>[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12}))?', UsersView.as_view()),
    url(r'^auth/(?P<mode>[a-z][a-z])', AuthSocial.as_view()),

]
