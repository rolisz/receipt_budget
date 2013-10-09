from django.db import models


class Shop(models.Model):
    name = models.CharField(max_length=50)
    address = models.TextField()
    cui = models.CharField(max_length=30, blank=True, verbose_name="C.U.I.")

    def __unicode__(self):
        return self.name + " at " + self.address


class Expense(models.Model):
    date = models.DateField('expense date')
    shop = models.ForeignKey(Shop)
    image = models.ImageField(upload_to='receipts/', null=True, blank=True)

    def __unicode__(self):
        return str(self.date) + " - " +  str(self.total) + " at " +\
               str(self.shop.name)


class ExpenseItem(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    category = models.CharField(max_length=50)
    expense = models.ForeignKey(Expense, null=True, default=None)

    def __unicode__(self):
        return self.name + " for " + str(self.price)
