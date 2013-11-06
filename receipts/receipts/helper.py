from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.core.urlresolvers import resolve
from receipts.models import Expense
from django.db.models import Sum, Avg

__author__ = 'Roland'


def menu_links(request):
    """
    Helper for determining active menu
    """
    links = []
    if request.user.is_authenticated():
        links += [
            ['Add expense', '/add/', ''],
            ['Show expenses', '/expenses/', ''],
            ['Dashboard', '/dashboard/', ''],
        ]

    for link in links:
        if link[1] in request.path:
            link[2] = 'active'
            break
    return {'links': links}


def current_expenses(request):
    """
    Helper for showing warning bar
    """
    if request.user.is_authenticated():
        try:
            avg = Expense.objects.for_user(request.user).aggregate(Sum('expenseitem__price'))['expenseitem__price__sum']/\
                  Expense.objects.for_user(request.user).count()
        except Exception:
            avg = 0
        avg = round(float(avg), 2)
        recent_expenses = Expense.objects.for_user(request.user).filter(date__gte=datetime.now()-timedelta(days=7))\
                                 .annotate(Sum('expenseitem__price'))
        if len(recent_expenses) != 0:
            recent_avg = round(float(sum(map(lambda x: x.expenseitem__price__sum or 0, recent_expenses))/len(recent_expenses)), 2)

            if recent_avg < avg * 0.75: # all fine and dandy
                return {}
            elif recent_avg < avg:  # we're still good, but we should tell the user we're getting close
                color = 'green'
            elif recent_avg < avg * 1.25:  # we should raise some alarms
                color = 'yellow'
            else:
                color = 'red'

            return {'color': color, 'avg': avg, 'recent': recent_avg}
    return {}

