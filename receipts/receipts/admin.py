from django.contrib import admin
from receipts.models import Expense, ExpenseItem, Shop
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe


class ExpenseItemInline(admin.StackedInline):
    model = ExpenseItem
    extra = 2

    template = 'admin/receipts/expense/item_stacked.html'

class ShopInline(admin.StackedInline):
    model = Shop

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

    def link(self, obj):
        print(obj.shop)
        url = reverse('admin:receipts_shop_change',args=(obj.shop.id,))
        print(url)
        return mark_safe("<a href='%s'>edit</a>" % url)

    link.allow_tags = True
    link.short_description = ""

    inlines = [ExpenseItemInline]
    fields = ['date', ('shop', 'link')]


class ShopAdmin(admin.ModelAdmin):

    class Media:
        css = {
            'all': ("receipts/css/bootstrap.css", "receipts/css/bootstrap-theme.css")
        }
        js = ("receipts/js/jquery.js", "receipts/js/bootstrap.min.js",)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_delete_link'] = True
        return super(ShopAdmin, self).change_view(request, object_id,
            form_url, extra_context=extra_context)


admin.site.register(Shop, ShopAdmin)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(ExpenseItem)
