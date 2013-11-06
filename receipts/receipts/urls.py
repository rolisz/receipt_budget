from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
    url(r'^$', views.index, name="index"),
    url(r'^expenses/$', views.expense_list, name="expense_list"),
    url(r'^add/', views.add_new_photo, name="add_expense"),
    url(r'^upload/', views.upload_photo, name="upload"),
    url(r'^upload_webcam/', views.upload_webcam),
    url(r'^csv/', views.import_csv, name="import_csv"),
    url(r'^dashboard/(.+?)$', views.dashboard, name="dashboard"),
    url(r'^dashboard/$', views.dashboard, name="dashboard", kwargs={'type': 'map'}),
)
