from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User

class UserExpenseManager(models.Manager):
    def for_user(self, user):
        return super(UserExpenseManager, self).get_query_set().filter(user=user)

class Shop(models.Model):
    name = models.CharField(max_length=50)
    address = models.TextField()
    cui = models.CharField(max_length=30, blank=True, verbose_name="C.U.I.")

    def __unicode__(self):
        return self.name + " at " + self.address


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

    total = property(_get_total)


class ExpenseItem(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    category = models.CharField(max_length=50, blank=True)
    expense = models.ForeignKey(Expense, null=True, default=None)

    def __unicode__(self):
        return self.name + " for " + str(self.price)
