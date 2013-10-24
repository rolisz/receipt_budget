from django.contrib import admin
from receipts.models import Expense, ExpenseItem, Shop


class ExpenseItemInline(admin.TabularInline):
    model = ExpenseItem
    extra = 2


class ExpenseAdmin(admin.ModelAdmin):
    inlines = [ExpenseItemInline]
    fields = ['date', 'shop']
    readonly_fields = ['image']

admin.site.register(Shop)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(ExpenseItem)
