from django.contrib import admin
from receipts.models import Expense, ExpenseItem, Shop


class ExpenseItemInline(admin.TabularInline):
    model = ExpenseItem
    extra = 2

    template = 'admin/receipts/expense/item_tabular.html'

class ExpenseAdmin(admin.ModelAdmin):
    class Media:
        css = {
            'all': ("receipts/css/bootstrap.css", "receipts/css/bootstrap-theme.css")
        }
        js = ("receipts/js/jquery.js", "receipts/js/bootstrap.min.js",)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_delete_link'] = True
        return super(ExpenseAdmin, self).change_view(request, object_id,
            form_url, extra_context=extra_context)

    inlines = [ExpenseItemInline]
    fields = ['date', 'shop']
    readonly_fields = ['image']

admin.site.register(Shop)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(ExpenseItem)
