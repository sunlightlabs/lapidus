from django.conf import settings
from lapidus.metrics.models import Unit, Project, Annotation, Metric, Observation, RatioObservation
from tastypie import fields
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from tastypie.http import HttpCreated, HttpNotImplemented
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
    
    def dehydrate(self, bundle):
        bundle.data['metric_name'] = bundle.obj.__unicode__()
        bundle.data['observation_class'] = bundle.obj.unit.observation_type.model
        return bundle
    
    def post_detail(self, request, **kwargs):
        pk = kwargs['pk'].strip("/")
        metric = Metric.objects.get(pk=pk)
        obs_class = metric.unit.observation_type.model_class()
        if obs_class is RatioObservation:
            return HttpNotImplemented()
        else:
            from_dt = iso8601.parse_date(request.POST['from_datetime']).replace(tzinfo=None)
            to_dt = iso8601.parse_date(request.POST['to_datetime']).replace(tzinfo=None)
            metric_obs = metric.related_observations
            try:
                ob = metric_obs.get(
                    metric = metric,
                    from_datetime = from_dt,
                    to_datetime = to_dt,
                )
            except obs_class.DoesNotExist:
                ob = obs_class.objects.create(
                    metric = metric,
                    from_datetime = from_dt,
                    to_datetime = to_dt,
                )
            rawvalue = request.POST.get('value', None)
            ob.value = self.deserialize(request, rawvalue)
            ob.save()
            url = "/observation/%s/" % ob.pk
            return HttpCreated(location=url)

class ObservationResource(ModelResource):
    metric = fields.ForeignKey(MetricResource, 'metric')

    def dehydrate(self, bundle):
        try:
            bundle.data.update({'value': bundle.obj.value})
        except:
            pass
        return bundle
        
    
    class Meta:
        authentication = KeyAuthentication()
        authorization = ProjectAuthorization()
        queryset = Observation.objects.all()
        resource_name = 'observation'

class MetricDetailResource(MetricResource):
    observations = fields.ToManyField(ObservationResource, 'related_observations', null=True, full=True)

