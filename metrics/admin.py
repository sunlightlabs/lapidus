from django.contrib import admin
from django.contrib.admin.util import unquote
from lapidus.metrics.models import Annotation, Metric, Observation, CountObservation, ListObservation, RatioObservation, Project, Unit

# import the logging library
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)


# units

class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'observation_unit', 'category', 'period')
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
    model = Observation

class CountObservationInline(admin.TabularInline):
    extra = 0
    model = CountObservation

class ListObservationInline(admin.TabularInline):
    extra = 0
    model = ListObservation

class RatioObservationInline(admin.TabularInline):
    extra = 0
    model = RatioObservation
    readonly_fields = ('from_datetime', 'to_datetime')


class MetricAdmin(admin.ModelAdmin):
    # inlines = []
    list_display = ('project', 'unit', 'is_cumulative')
    list_display_links = ('project', 'unit')
    list_filter = ('project', 'is_cumulative', 'unit', 'unit__category')
    
    def add_view(self, request, form_url='', extra_context=None):
        self.inlines = []
        self.inline_instances = []
        return super(MetricAdmin, self).add_view(request, form_url, extra_context)
    
    def change_view(self, request, object_id, extra_context=None):
        logger.debug('change_view had inlines: {inlines}'.format(inlines=self.inlines))
        self.append_inline_class_and_instance(request, object_id)        
        return super(MetricAdmin, self).change_view(request, object_id, extra_context)
        
    def get_inline_instances(self, request):
        inline_instances = self.generate_inline_instances()
        return inline_instances

    def append_inline_class_and_instance(self, request, object_id):
        obj = self.get_object(request, unquote(object_id))
        model_class = obj.unit.observation_type.model_class()
        observation_inlines = {
                CountObservationInline.model: CountObservationInline, 
                ListObservationInline.model : ListObservationInline, 
                RatioObservationInline.model: RatioObservationInline
        }
        inline_class = observation_inlines[model_class]
        self.inlines = [inline_class,]
        # if inline_class not in self.inlines:
        #     self.inlines.append(inline_class)
        if hasattr(self, 'inline_instances'):
            # This works in Django 1.3 and lower
            # In Django 1.4 inline instances are generated using overridden get_inline_instances()
            self.inline_instances = self.generate_inline_instances()
        
        logger.debug('Appended inlines: {inlines}'.format(inlines=self.inlines))
    
    def generate_inline_instances(self):
        inline_instances = []
        for inline_class in self.inlines:
            inline_instance = inline_class(self.model, self.admin_site)
            inline_instances.append(inline_instance)
        return inline_instances
        
admin.site.register(Metric, MetricAdmin)