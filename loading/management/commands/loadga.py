from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from googleanalytics import Connection
from loading import ga
from lapidus.metrics.models import Project, Metric, Unit, Observation
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
    
    
    def _generate_list_payload(self, data, limit=None):
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
                        try:
                            u = Unit.objects.get(name=metric['name'])
                        except Unit.DoesNotExist:
                            u = Unit.objects.create(name=metric['name'], slug=slugify(metric['name']), category=1, period=1)
                            if verbosity >= 2:
                                self.stdout.write('Saving Unit "{0}\n"'.format(u.name))
                            self._save_object(u)
                        try:
                            m = p.metrics.get(unit=u)
                        except Metric.DoesNotExist:
                            m = Metric.objects.create(project=p, unit=u, type=metric.get('type', 'value'))
                            if verbosity >= 2:
                                self.stdout.write('Saving Metric "{0}" for "{1}\n"'.format(u.name, p.name))
                            self._save_object(m)
                        
                        data = acct.get_data(
                            start_date=yesterday.date(),
                            end_date=yesterday.date(),
                            metrics=metric['metrics'],
                            dimensions=metric.get('dimensions', None)
                        )
                        
                        try:
                            
                            o = Observation.objects.get(
                                metric=m,
                                from_datetime=start,
                                to_datetime=end,
                            )
                            # if m.type = list, we need to generate a list of objects with rank & name k/v pairs, and possibly a value k/v from the data returned...
                            if m.type is 'list':
                                o.payload = self._generate_list_payload(data)
                            else:
                                o.value = data[0].metrics[0].value
                            if verbosity >= 2:
                                self.stdout.write('Saving Observation for metric"{0}" at "{1}" with \npayload:\n{2}\nvalue:\n{3}\n'.format(u.name, start, o.payload, o.value))
                            self._save_object(o)
                        
                        except Observation.DoesNotExist:
                            
                            o = Observation.objects.create(
                                metric=m,
                                from_datetime=start,
                                to_datetime=end,
                            )
                            if m.type is 'list':
                                o.payload = self._generate_list_payload(data)
                            else:
                                o.value = data[0].metrics[0].value
                            self._save_object(o)
            
            except Project.DoesNotExist:
                raise CommandError( "{0} project is not found".format(project['slug']) )