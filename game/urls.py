from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.game, name='game'),
    url(r'^list/', views.answer_list, name='answer_list'),
    url(r'^(?P<pk>\d+)/$', views.answer_detail, name='answer_detail'),
    url(r'^new/$', views.answer_create, name='answer_create'),
    url(r'^playing/$', views.get_result, name='get_result'),
]
