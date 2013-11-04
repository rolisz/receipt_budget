import datetime
from django.core.exceptions import ValidationError
from django.core.files.storage import Storage, FileSystemStorage
from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver
from geopy.geocoders import GoogleV3


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
        return self.name + ((" at " + self.address) if self.address else "")


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
        s = FileSystemStorage()
        img = s.save(image.name, image)
        print(s.path(img))
        #print(type(s.path(img)))
        rec = Receipt(s.path(img))
        rec.analyze_text()
        props = {'shop':'SC ARTIMA SA', 'address':"STR IZLAZULUI", "items":[("APA DORNA", 3.2)], 'total':3.2,
                 'cui':'0124345', 'data':'2013-10-10'}
        props = rec.props
        print(props)
        shop = Shop.objects.get_or_create(name=props['shop'], address=props['address'], cui=props['cui'])[0]
        try:
            exp = shop.expense_set.create(date=props['data'], user=user, image=img)
        except ValidationError:
            exp = shop.expense_set.create(date=datetime.date.today(), user=user, image=img)
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
    print(instance.lat, instance.lon)
    try:
        obj = Shop.objects.get(pk=instance.pk)
    except Shop.DoesNotExist:
        pass
    if obj.address != instance.address:
        if instance.address not in ["", "unknown"]:
            address, (latitude, longitude) = geolocator.geocode(instance.address, exactly_one=False)[0]
            instance.lat = latitude
            instance.lon = longitude
    elif obj.lat != instance.lat or obj.lon != instance.lat:
        address, (latitude, longitude) = geolocator.reverse(instance.lat, instance.long, exactly_one=False)[0]
        instance.address = address

