from django.conf import settings
from lapidus.metrics.models import Unit, Project, Annotation, Metric, Observation
from tastypie import fields
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from tastypie.http import HttpCreated
from tastypie.resources import ModelResource
import iso8601

#
# authentication and authorization
#

class KeyAuthentication(Authentication):
    
    def is_authenticated(self, request, **kwargs):
        
        api_key = request.META.get('HTTP_X_APIKEY', None)
        
        if api_key == getattr(settings, "API_MASTER_KEY", None):
            request.project = "*"
        else:
            try:
                request.project = Project.objects.get(api_key=api_key)
            except Project.DoesNotExist:
                request.project = None
        
        return request.project is not None
    
    def get_identifier(self, request):
        
        api_key = request.META.get('HTTP_X_APIKEY', '')
        
        try:
            project = Project.objects.get(api_key=api_key)
            identifier = project.name
        except Project.DoesNotExist:
            identifier = None
        
        return identifier

class ProjectAuthorization(Authorization):

    def is_authorized(self, request, object=None):
        return request.project is not None

    def apply_limits(self, request, object_list):
        if request is None or request.project == "*":
            return object_list
        elif object_list.model == Project:
            return object_list.filter(pk=request.project.pk)
        elif object_list.model == Metric or object_list.model == Annotation:
            return object_list.filter(project=request.project)
        elif object_list.model == Observation:
            return object_list.filter(metric__project=request.project)
        else:
            return object_list.none()

#
# resources
#

class ProjectResource(ModelResource):
    class Meta:
        authentication = KeyAuthentication()
        authorization = ProjectAuthorization()
        queryset = Project.objects.all()
        resource_name = 'project'
    
    def dehydrate(self, bundle):
        bundle.data['metrics'] = [MetricResource().full_dehydrate(m) for m in bundle.obj.metrics.all()]
        bundle.data['annotations'] = [AnnotationResource().full_dehydrate(a) for a in bundle.obj.annotations.all()]
        return bundle

class AnnotationResource(ModelResource):
    project = fields.ForeignKey(ProjectResource, 'project')
    class Meta:
        authentication = KeyAuthentication()
        authorization = ProjectAuthorization()
        queryset = Annotation.objects.all()
        resource_name = 'annotation'

class MetricResource(ModelResource):
    
    project = fields.ForeignKey(ProjectResource, 'project')
    
    class Meta:
        authentication = KeyAuthentication()
        authorization = ProjectAuthorization()
        queryset = Metric.objects.all()
        resource_name = 'metric'
    
    def post_detail(self, request, **kwargs):
        pk = kwargs['pk'].strip("/")
        metric = Metric.objects.get(pk=pk)
        from_dt = iso8601.parse_date(request.POST['from_datetime']).replace(tzinfo=None)
        to_dt = iso8601.parse_date(request.POST['to_datetime']).replace(tzinfo=None)
        try:
            ob = Observation.objects.get(
                metric = metric,
                from_datetime = from_dt,
                to_datetime = to_dt,
            )
        except Observation.DoesNotExist:
            ob = Observation.objects.create(
                metric = metric,
                from_datetime = from_dt,
                to_datetime = to_dt,
            )
        ob.value = request.POST.get('value', None)
        ob.payload = request.POST.get('payload', '')
        ob.save()
        url = "/observation/%s/" % ob.pk
        return HttpCreated(location=url)

class MetricDetailResource(MetricResource):
    def dehydrate(self, bundle):
        bundle.data['observations'] = [ObservationResource().full_dehydrate(ob) for ob in bundle.obj.observations.all()]
        return bundle

class ObservationResource(ModelResource):
    metric = fields.ForeignKey(MetricResource, 'metric')
    class Meta:
        authentication = KeyAuthentication()
        authorization = ProjectAuthorization()
        queryset = Observation.objects.all()
        resource_name = 'observation'