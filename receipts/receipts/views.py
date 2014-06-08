import StringIO
import base64
from itertools import groupby
import json
import os
import string
import random
import cv2
from dateutil.parser import parse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
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
    image = request.FILES['photo']
    s = FileSystemStorage()
    img = s.save(image.name, image)
    print(s.path(img))
    exp = Expense.from_receipt(s.path(img), request.user)
    return redirect(reverse('admin:receipts_expense_change', args=(exp.id,)))


def index(request):
    if request.user.is_authenticated():
        expenses = Expense.objects.for_user(request.user).all()
        return render(request, 'receipts/expense_list.html', {'expenses':expenses})
    else:
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
                try:
                    s = Shop.objects.get(name__contains=kv['place'])
                except Shop.DoesNotExist:
                    s = Shop.objects.create(name=kv['place'])
                except Shop.MultipleObjectsReturned:
                    s = Shop.objects.filter(name__contains=kv['place'])[0]
            date = parse(kv['date'], dayfirst=True)
            print(s)
            exp = s.expense_set.create(date=date, user=request.user)
            price = re.match("(\d+([.,]\d+)?)", kv['price'])
            if not price:
                print("Invalid price %s" % kv['price'])
                continue
            price = price.groups()[0].replace(',', '.')
            exp.expenseitem_set.create(name=kv['item'], price=price)

        return HttpResponse("Success!")

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

@login_required()
def upload_webcam(request):
    """
    Generate a random name for the photo and save it to disk, then crop it and extract information
    """
    name = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(10)) + ".png"
    path = os.path.join(settings.MEDIA_ROOT, name)
    f = open(path, "wb")
    img_string = request.POST['photo'][22:]
    img_data = img_string.decode("base64")
    f.write(img_data)
    f.close()
    img = cv2.imread(path)
    x1, y1, x2, y2 = (int(request.POST['x1']), int(request.POST['y1']),
                      int(request.POST['x2']), int(request.POST['y2']))
    img = img[y1:y2, x1:x2]
    cv2.imwrite(path, img)
    try:
        exp = Expense.from_receipt(path, request.user)
        return redirect(reverse('admin:receipts_expense_change', args=(exp.id,)))
    except Exception:
        return render(request, 'receipts/add_photo.html', {'error': "Couldn't find a receipt in the image!"})