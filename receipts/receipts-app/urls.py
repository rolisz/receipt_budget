from django.conf.urls import patterns, include, url

from django.contrib import admin
import receipts #, receipts.line
admin.autodiscover()

urlpatterns = patterns('',
    url(r'', include('receipts.urls')),
    url(r'^$', include('receipts.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('userena.urls'), name="userena"),
)
