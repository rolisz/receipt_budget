from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.core.urlresolvers import resolve
from receipts.models import Expense
from django.db.models import Sum, Avg

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
    return {'links': links}


def current_expenses(request):
    if request.user.is_authenticated():
        avg = Expense.objects.for_user(request.user).aggregate(Sum('expenseitem__price'))['expenseitem__price__sum']/\
              Expense.objects.for_user(request.user).count()
        avg = round(float(avg), 2)
        recent_expenses = Expense.objects.for_user(request.user).filter(date__gte=datetime.now()-timedelta(days=7))\
                                 .annotate(Sum('expenseitem__price'))
        recent_avg = round(float(sum(map(lambda x: x.expenseitem__price__sum, recent_expenses))/len(recent_expenses)), 2)
        if recent_avg < avg * 0.75: # all fine and dandy
            return {}
        elif recent_avg < avg:  # we're still good, but we should tell the user we're getting close
            color = 'green'
        elif recent_avg < avg * 1.25:  # we should raise some alarms
            color = 'yellow'
        else:
            color = 'red'
        print(avg, recent_avg)
        return {'color': color, 'avg': avg, 'recent': recent_avg}
    return {}

