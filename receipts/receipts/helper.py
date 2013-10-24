from django.contrib.auth.models import User
from django.core.urlresolvers import resolve

__author__ = 'Roland'


def menu_links(request):
    links = []
    if request.user.is_authenticated():
        links += [
            ['Add expense', '/add/', ''],
            ['Show expenses', '/expenses/', ''],
        ]

    for link in links:
        if request.path == link[1]:
            link[2] = 'active'
            break
    return { 'links': links }