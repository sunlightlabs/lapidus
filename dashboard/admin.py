from django.contrib import admin
from django.forms import ModelForm
from models import UnitCollection, OrderedMembership


class OrderedMembershipInline(admin.TabularInline):
    model = OrderedMembership
    extra = 1
    ordering = ['order']

class UnitCollectionFormModelForm(ModelForm):
    """(UnitCollectionForm description)"""
    
    class Media:
        js = (
            "dashboard/js/jquery-1.6.2.min.js",
            "dashboard/js/jquery-ui-1.8.16.custom.min.js",
            "dashboard/js/orderable.jquery.js",
        )

    def __unicode__(self):
        return u"UnitCollectionForm"


class UnitCollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'list_of_units',)
    form = UnitCollectionFormModelForm
    prepopulated_fields = {'slug': ('name',)}
    inlines = [
        OrderedMembershipInline,
    ]

admin.site.register(UnitCollection, UnitCollectionAdmin)


# class OrderedMembershipAdmin(admin.ModelAdmin):
#     list_display = ('collection', 'unit', 'order')
#     # list_filter = ('',)
#     # search_fields = ('',)
# 
# 
# admin.site.register(OrderedMembership, OrderedMembershipAdmin)