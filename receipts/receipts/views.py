from itertools import groupby
import json
from dateutil.parser import parse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.views.generic import ListView

from receipts.models import Shop, Expense, ExpenseItem
#from receipts.receipt import Receipt
import re
from geopy.geocoders import GoogleV3
from tokenapi.http import JsonResponse


@login_required
def add_new_photo(request):
    return render(request, 'receipts/add_photo.html')


@login_required
def upload_photo(request):
    exp = Expense.from_receipt(request.FILES['photo'], request.user)
    return redirect(reverse('admin:receipts_expense_change', args=(exp.id,)))


def index(request):
    return render(request, 'receipts/index.html')


@login_required
def expense_list(request):
    expenses = Expense.objects.for_user(request.user).all()
    return render(request, 'receipts/expense_list.html', {'expenses':expenses})


@login_required
def import_csv(request):
    if request.method == 'POST':
        rows = json.loads(request.POST['csv'])
        headers = rows[0]
        for row in rows[1:]:
            kv = dict(zip(headers, row))
            if len(kv['place'].strip()) == 0:
                s = Shop.objects.get(name='unknown')
            else:
                s = Shop.objects.get_or_create(name=kv['place'])[0]
            date = parse(kv['date'], dayfirst=True, yearfirst=True) # not good!
            print(s)
            exp = s.expense_set.create(date=date, user=request.user)
            price = re.match("(\d+([.,]\d+))", kv['price'])
            if not price:
                print("Invalid price %s" % kv['price'])
                continue
            price = price.groups()[0]
            exp.expenseitem_set.create(name=kv['item'], price=price)

        return HttpResponse("Huge success!")

    return render(request, 'receipts/import_csv.html', {})

@login_required
def dashboard(request, type):
    print(type)
    if type == 'map':
        return render(request, 'receipts/dashboard.html', {})
    elif type == 'day':
        return render(request, 'receipts/dashboard_day.html', {})
    elif type == 'graph':
        return render(request, 'receipts/dashboard_dc.html', {})
