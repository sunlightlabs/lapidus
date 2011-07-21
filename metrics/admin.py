from django.contrib import admin
from lapidus.metrics.models import Annotation, Metric, Observation, Project, Unit

# units

class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'category', 'period')
    list_display_links = ('name',)
    list_filter = ('category', 'period')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

admin.site.register(Unit, UnitAdmin)

# projects

class AnnotationInline(admin.TabularInline):
    extra = 0
    model = Annotation

class ProjectAdmin(admin.ModelAdmin):
    inlines = (AnnotationInline,)
    list_display = ('name', 'slug', 'api_key')
    list_display_links = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    
admin.site.register(Project, ProjectAdmin)

# metrics

class ObservationInline(admin.TabularInline):
    extra = 0
    model = Observation

class MetricAdmin(admin.ModelAdmin):
    inlines = (ObservationInline,)
    list_display = ('project', 'unit', 'is_cumulative')
    list_display_links = ('project', 'unit')
    list_filter = ('is_cumulative',)

admin.site.register(Metric, MetricAdmin)