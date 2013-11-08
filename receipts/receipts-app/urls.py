from django.conf.urls import patterns, include, url

from django.contrib import admin
import receipts #, receipts.line
admin.autodiscover()

urlpatterns = patterns('',
    url(r'', include('receipts.urls')),
    url(r'^$', include('receipts.urls')),
    url(r'', include('tokenapi.urls')),
    url(r'^admin/receipts/expense/$', 'receipts.views.expense_list'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^rest/', include('rest_receipts.urls')),
    url(r'^accounts/', include('userena.urls'), name="userena"),
)
