import json
from dateutil.parser import parse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.views.generic import ListView

from receipts.models import Shop, Expense, ExpenseItem
#from receipts.receipt import Receipt
import re


@login_required
def add_new_photo(request):
    return render(request, 'receipts/add_photo.html')

@login_required
def upload_photo(request):
    with open('image.jpg', 'wb') as destination:
        for chunk in request.FILES['photo'].chunks():
            destination.write(chunk)
    rec = Receipt('image.jpg')
    rec.analyze_text()
    #props = {'shop':'SC ARTIMA SA', 'address':"STR IZLAZULUI", "items":[("APA DORNA", 3.2)], 'total':3.2,
    #         'cui':'0124345', 'data':'2013-10-10'}
    props = rec.props
    print(props)
    shop = Shop.objects.get_or_create(name=props['shop'], address=props['address'], cui=props['cui'])[0]
    try:
        exp = shop.expense_set.create(date=props['data'], user=request.user)
    except ValidationError:
        exp = shop.expense_set.create(date='2013-10-10', user=request.user)
    for it, price in props['items']:
        exp.expenseitem_set.create(name=it, price=price)
    return redirect(reverse('admin:receipts_expense_change', args=(exp.id,)))


def index(request):
    return render(request, 'receipts/index.html')

def expense_list(request):
    expenses = Expense.objects.for_user(request.user).all()
    return render(request, 'receipts/expense_list.html', {'expenses':expenses})

def edit_receipt(request, receipt_id):
    receipt = get_object_or_404(Expense, id=receipt_id)
    return render(request, 'receipts/edit_receipt.html', {'receipt': receipt})


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