from django.contrib import admin
from django.contrib.admin.util import unquote
from django.contrib.contenttypes import generic
from django.utils.functional import curry
from django.forms import ModelForm
from dashboard.models import *

class OrderedListModelForm(ModelForm):
    class Media:
        js = (
            "dashboard/js/jquery-1.6.2.min.js",
            "dashboard/js/jquery-ui-1.8.16.custom.min.js",
            "dashboard/js/orderable.jquery.js",
        )

    def __unicode__(self):
        return u"OrderedListModelForm"

class OrderedListMembershipInline(admin.TabularInline):
    extra = 1
    ordering = ['order']
    classes = ('orderedinline',)

class OrderedListAdmin(admin.ModelAdmin):
    list_display = ('name', 'default_for')
    form = OrderedListModelForm
    prepopulated_fields = {'slug': ('name',)}


# UnitList Admin
class UnitListMembershipInline(OrderedListMembershipInline):
    model = UnitListMembership

class UnitListAdmin(OrderedListAdmin):
    inlines = [
        UnitListMembershipInline,
    ]

admin.site.register(UnitList, UnitListAdmin)

# ProjectList Admin
class ProjectListMembershipInline(OrderedListMembershipInline):
    model = ProjectListMembership

class ProjectListAdmin(OrderedListAdmin):
    inlines = [
        ProjectListMembershipInline,
    ]

admin.site.register(ProjectList, ProjectListAdmin)


# MetricList Admin
class MetricListMembershipInline(OrderedListMembershipInline):
    model = MetricListMembership

class MetricListAdmin(OrderedListAdmin):
    inlines = [
        MetricListMembershipInline,
    ]

admin.site.register(MetricList, MetricListAdmin)
