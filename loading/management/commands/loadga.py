from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.contenttypes.models import ContentType
from googleanalytics import Connection
from lapidus.metrics.models import Project, Metric, Unit, CountObservation, ListObservation
import datetime
import logging
import json

class Command(BaseCommand):
    help = 'Load latest stats from Google Analytics'
    
    def _save_object(self, obj):
        try:
            obj.full_clean()
        except ValidationError, e:
            raise CommandError("[%s]:\n\t%s" % (obj, ', '.join(e.messages)))
        try:
            obj.save()
        except IntegrityError, e:
            raise CommandError("[%s]:\n\t%s" % (obj, ','.join(e.messages)))
    
    def _generate_list(self, data, limit=None):
        sorteddata = sorted(data, lambda x,y: cmp(x.metrics[0].value,y.metrics[0].value), None, True)
        return [ { 'rank': n, 'name': d.dimensions[0].value, 'value': d.metrics[0].value } for n,d in enumerate(sorteddata) ][:limit]
    
    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity'))
        
        config = json.load(open(settings.GA_CONFIG))
        conn = Connection(settings.GA_EMAIL, settings.GA_PASSWORD)
        
        yesterday = datetime.datetime.now() - datetime.timedelta(1)
        start = datetime.datetime.combine(yesterday.date(), datetime.time(0, 0, 0))
        end = datetime.datetime.combine(yesterday.date(), datetime.time(23, 59, 59))
        
        for project in config['projects']:
            
            try:
                
                p = Project.objects.get(slug=project['slug'])
                
                if project.has_key('profile_id'):
                    
                    acct = conn.get_account(project['profile_id']) # profile_id
                    
                    metrics = config['defaults']['metrics']
                    if project.get('metrics'):
                        metrics += project.get('metrics')
                    
                    for metric in metrics:
                        # Check for existence of Unit and Metric and create if needed.
                        content_type = ContentType.objects.get(app_label='metrics', model= metric.get('type', 'count')+'observation')
                        observation_class = content_type.model_class()
                        try:
                            u = Unit.objects.get(name=metric['name'])
                        except Unit.DoesNotExist:
                            u = Unit.objects.create(name=metric['name'], slug=slugify(metric['name']), category=1, period=1)
                            if verbosity >= 2:
                                self.stdout.write('Unit "{0}\n"'.format(u.name))
                        self._save_object(u)
                        
                        try:
                            m = p.metrics.get(unit=u)
                        except Metric.DoesNotExist:
                            m = Metric.objects.create(project=p, unit=u, observation_type=content_type)
                        self._save_object(m)
                        if verbosity >= 2:
                            self.stdout.write('Metric "{name}" of type "{content_type}" for "{project}"\n'.format(name=u.name, project=p.name, content_type=content_type))
                        
                        data = acct.get_data(
                            start_date=yesterday.date(),
                            end_date=yesterday.date(),
                            metrics=metric['metrics'],
                            dimensions=metric.get('dimensions', None)
                        )
                        
                        try:
                            o = observation_class.objects.get(
                                metric=m,
                                from_datetime=start,
                                to_datetime=end,
                            )
                            # if m.type = list, we need to generate a list of objects with rank & name k/v pairs, and possibly a value k/v from the data returned...
                        except observation_class.DoesNotExist:
                            o = observation_class.objects.create(
                                metric=m,
                                from_datetime=start,
                                to_datetime=end,
                            )
                        if observation_class is ListObservation:
                            o.value = self._generate_list(data)
                        else:
                            o.value = float(data[0].metrics[0].value)
                        if verbosity >= 2:
                            self.stdout.write('Observation for metric "{0}" at "{1}" with value:\n{2}\n'.format(u.name, start, o.value))
                        self._save_object(o)
            
            except Project.DoesNotExist:
                raise CommandError( "{0} project is not found".format(project['slug']) )