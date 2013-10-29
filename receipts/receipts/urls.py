from django.conf.urls import patterns, include, url
import views
urlpatterns = patterns('',
    url(r'^$', views.index, name="index"),
    url(r'^expenses/$', views.expense_list, name="expense_list"),
    #url(r'^edit_receipt/(\d+)', views.edit_receipt, name="edit_receipt"),
    url(r'^add/', views.add_new_photo, name="add_expense"),
    url(r'^upload/', views.upload_photo, name="upload"),
    url(r'^csv/', views.import_csv, name="import_csv"),
    url(r'^expenses/day.json', views.expense_list_day_json, name="day_json"),

)
