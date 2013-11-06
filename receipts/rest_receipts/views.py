from itertools import groupby
import json
from receipts.models import Expense, Shop
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from geopy.geocoders import GoogleV3
from tokenapi.decorators import token_required
from tokenapi.http import JsonError, JsonResponse


@token_required
@csrf_exempt
def add(request):
    print(request.POST)
    print(request.FILES)
    exp = Expense.from_receipt(request.FILES['photo'], request.user)
    print(exp)
    expense = [exp.id, str(exp.date), str(exp.shop), []]
    for item in exp.expenseitem_set.all():
        expense[-1].append((item.name, str(item.price), item.category))
    return JsonResponse(expense)


@token_required
def edit(request, id):
    if request.method != "POST":
        return JsonError("Only POST is allowed")
    post = request.POST
    try:
        exp = Expense.objects.get(pk=id)
        if post['shop'] != exp.shop:
            shop = Shop.objects.get_or_create(name=post['shop'])[0]
            exp.shop = shop
        exp.date = post['date']
        exp.expenseitem_set.clear()
        for name, price, category in json.loads(post['items']):
            exp.expenseitem_set.create(name=name, price=price, category=category)
        exp.save()
        print(exp)
        exp = Expense.objects.get(pk=id)
        print(exp)
    except KeyError as e:
        return JsonError("The following key is not found %s" % e)
    except Expense.DoesNotExist:
        return JsonError("Invalid id")
    return JsonResponse({})


@token_required
def delete(request, id):
    if request.method != "POST":
        return JsonError("Only POST is allowed")
    post = request.POST
    try:
        exp = Expense.objects.get(pk=id)
        print(exp)
        exp.delete()
    except Expense.DoesNotExist:
        return JsonError("Invalid id")
    return JsonResponse({})


@token_required
def index(request):
    print(request.user)
    expenses = Expense.objects.for_user(request.user).all()
    l = listify(expenses)
    return JsonResponse(l)


@login_required
def expense_list_json(request, type):
    print(request.user)
    expenses = Expense.objects.for_user(request.user)

    if type == 'all':
        expenses = expenses.all()
        groups = listify(expenses)
    elif type == 'place':
        shops = Shop.objects.filter(lat__isnull=False, lon__isnull=False).annotate(Sum('expense__expenseitem__price'))
        groups = []
        for shop in shops:
            groups.append((shop.name, shop.lat, shop.lon, shop.expense__expenseitem__price__sum))
    elif type == 'day':
        expenses = expenses.order_by('date').all()
        groups = []
        for k, g in groupby(expenses, lambda x: x.date):
            groups.append((str(k), listify(g)))
    else:
        JsonError("Invalid request")
    return JsonResponse(groups)


def listify(expenses):
    listified = []
    for exp in expenses:
        expense = {'id': exp.id, 'shop': str(exp.shop.name), 'lat': exp.shop.lat, 'lon': exp.shop.lon,
                   'total': exp.total, 'date': str(exp.date)}
        listified.append(expense)
    return listified