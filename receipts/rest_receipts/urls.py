from django.conf.urls import patterns, include, url
from rest_receipts import views

__author__ = 'Roland'
urlpatterns = patterns(
    '',
    url(r'^expense/add/', views.add),
    url(r'^expense/index/', views.index),
    url(r'^expense/edit/(\d+)', views.edit),
    url(r'^expense/delete/(\d+)', views.delete),
    url(r'^expenses/(.+?).json', views.expense_list_json, name="day_json"),
    url(r'^expenses/(.+?).json', views.expense_list_json, name="all_json"),
)