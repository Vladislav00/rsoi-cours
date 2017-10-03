"""agregator URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url

from home.views import redeem_view, sign_view, ShopView, admin_prefs, admin_home, admin_fabric, admin_user, admin_prize, \
    admin_order, me_orders_view, me_view

urlpatterns = [
    url(r'^sign(/(?P<action>(reg|auth)))?', sign_view),
    url(r'^shop(/(?P<prize>available|[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12}))?', ShopView.as_view(), name='home'),
    url(r'^me/orders', me_orders_view),
    url(r'^me', me_view),
    url(r'^admin/preferences', admin_prefs),
    url(r'^admin/fabric', admin_fabric),
    url(
        r'admin/user(/((?P<create>create)|((?P<user>[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12})(/(?P<delete>delete))?)))?',
        admin_user),
    url(
        r'admin/prize(/((?P<create>create)|((?P<prize>[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12})(/(?P<delete>delete))?)))?',
        admin_prize),
    url(
        r'admin/order(/((?P<create>create)|((?P<order>[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12})(/(?P<delete>delete))?)))?',
        admin_order),

    url(r'^admin', admin_home),
    url(r'^redeem', redeem_view),
    url(r'', ShopView.as_view(), name='home'),
]
