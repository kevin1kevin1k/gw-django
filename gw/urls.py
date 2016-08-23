"""gw URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
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
from django.conf.urls import url,include
from django.contrib import admin
from stores.views import store_list, store_detail
from pages.views import home
from game.views import game

urlpatterns = [
    url(r'^$', home, name="home"),
    url(r'^store/', include('stores.urls')),
    url(r'^game/', include('game.urls')),
    # url(r'^store/$', store_list, name='store_list'),
    # url(r'^store/(?P<pk>\d+)/$', store_detail, name='store_detail'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('django.contrib.auth.urls')),
]
