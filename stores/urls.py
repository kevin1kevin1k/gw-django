from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.store_list, name='store_list'),
    url(r'^(?P<pk>\d+)/$', views.store_detail, name='store_detail'),
    url(r'^new/$', views.store_create, name='store_create'),
    url(r'^(?P<pk>\d+)/update/$', views.store_update, name='store_update'),
]
