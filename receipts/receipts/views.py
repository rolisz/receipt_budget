from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.http import Http404
from django.views.generic import ListView

from receipts.models import Shop, Expense, ExpenseItem
#from receipts.receipt import Receipt


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
        pass

    return render(request, 'receipts/import_csv.html', {})