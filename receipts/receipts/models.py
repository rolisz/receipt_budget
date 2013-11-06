from collections import namedtuple
import datetime
from django.core.exceptions import ValidationError
from django.core.files.storage import Storage, FileSystemStorage
from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver
from geopy.geocoders import GoogleV3
from geopy.geocoders.googlev3 import GQueryError


class UserExpenseManager(models.Manager):
    def for_user(self, user):
        return super(UserExpenseManager, self).get_query_set().filter(user=user)

class Shop(models.Model):
    name = models.CharField(max_length=50)
    address = models.TextField(blank=True)
    cui = models.CharField(max_length=30, blank=True, verbose_name="C.U.I.")
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)

    def __unicode__(self):
        if self.address != 'unknown':
            return self.name + ((" at " + self.address) if self.address else "")
        else:
            return self.name


class Expense(models.Model):

    objects = UserExpenseManager()
    date = models.DateField('expense date')
    shop = models.ForeignKey(Shop)
    image = models.ImageField(upload_to='receipts/', null=True, blank=True)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return str(self.date) + " - " + str(self.total) + " at " +\
               str(self.shop.name)

    def _get_total(self):
        return self.expenseitem_set.all().aggregate(Sum('price'))['price__sum']

    @classmethod
    def from_receipt(cls, image, user):
        from receipts.receipt import Receipt
        rec = Receipt(image)
        rec.analyze_text()
        props = rec.props
        print(props)
        shop = Shop.objects.get_or_create(name=props['shop'], address=props['address'], cui=props['cui'])[0]
        try:
            exp = shop.expense_set.create(date=props['data'], user=user, image=image)
        except ValidationError:
            exp = shop.expense_set.create(date=datetime.date.today(), user=user, image=image)
        for it, price in props['items']:
            exp.expenseitem_set.create(name=it, price=price)
        return exp

    total = property(_get_total)


class ExpenseItem(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    category = models.CharField(max_length=50, blank=True)
    expense = models.ForeignKey(Expense, null=True, default=None)

    def __unicode__(self):
        return self.name + " for " + str(self.price)

geolocator = GoogleV3()
@receiver(pre_save, sender=Shop)
def my_handler(sender, instance, **kwargs):
    """
    When editing a shop, do a geocoding request if address changed
    """
    try:
        obj = Shop.objects.get(pk=instance.pk)
    except Shop.DoesNotExist:
        obj = namedtuple('Shop', ['address'])
        obj.address = ""
    if obj.address != instance.address:
        if instance.address not in ["", "unknown"]:
            try:
                address, (latitude, longitude) = geolocator.geocode(instance.address, exactly_one=False)[0]
                instance.lat = latitude
                instance.lon = longitude
            except GQueryError:
                pass
    elif obj.lat != instance.lat or obj.lon != instance.lat:
        address, (latitude, longitude) = geolocator.reverse(instance.lat, instance.long, exactly_one=False)[0]
        instance.address = address

