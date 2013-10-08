from django.db import models

class Receipt(models.Model):
    date = models.DateField('expense date')
    location = models.CharField(max_length=50)
    image = models.ImageField(upload_to='receipts/', null=True, blank=True)

class Category(models.Model):
    name = models.CharField(max_length=50)

class Expense(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    category = models.ForeignKey(Category)
    receipt = models.ForeignKey(Receipt, null=True, default=None)
