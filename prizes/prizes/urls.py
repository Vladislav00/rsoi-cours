"""prizes URL Configuration

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
from django.conf.urls.static import static

from prize.views import PrizeView, OrderView
from prizes import settings

urlpatterns = [
    url(r'^prize(\/(?P<prize>[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12})?)?$', PrizeView.as_view()),
    url(r'^order(\/(?P<order>[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12})?)?$', OrderView.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

