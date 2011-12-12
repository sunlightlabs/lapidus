from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.contenttypes.models import ContentType
from googleanalytics import Connection
from lapidus.metrics.models import Project, Metric, Unit, CountObservation, ObjectObservation, UNIT_TYPES
import datetime
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


DATE_FORMAT = "%Y-%m-%d"

class Command(BaseCommand):
    help = 'Load stats from Google Analytics. Defaults to latest available (yesterday), but can be given a particular date or a date range'
    args = '[from_date] [to_date]'
    
    def _generate_sorted_list(self, data, limit=None):
        sorteddata = sorted(data, lambda x,y: cmp(x.metrics[0].value,y.metrics[0].value), None, True)
        return [ { 'rank': n, 'name': d.dimensions[0].value, 'value': d.metrics[0].value } for n,d in enumerate(sorteddata) ][:limit]
    
    def _save_object(self, obj):
        try:
            obj.full_clean()
        except ValidationError, e:
            raise CommandError("[%s]:\n\t%s" % (obj, ', '.join(e.messages)))
        try:
            obj.save()
        except IntegrityError, e:
            raise CommandError("[%s]:\n\t%s" % (obj, ','.join(e.messages)))
    
    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity'))
        
        if len(args):
            from_date = datetime.datetime.strptime(args[0], DATE_FORMAT)
        else:
            from_date = datetime.datetime.now() - datetime.timedelta(1)
        
        if len(args) > 1:
            to_date = datetime.datetime.strptime(args[1], DATE_FORMAT)
            datedelta = to_date - from_date
        else:
            to_date = datedelta = None
        
        if verbosity >= 2:
            self.stdout.write("from_date: {0}\n".format(from_date))
            self.stdout.write("to_date  : {0}\n".format(to_date))
        
        dates = [from_date]
        
        if datedelta:
            dates += [from_date + datetime.timedelta(days=r) for r in range(1, datedelta.days+1)]
        
        config = json.load(open(settings.GA_CONFIG))
        conn = Connection(settings.GA_EMAIL, settings.GA_PASSWORD)
        
        for aday in dates:
            start = datetime.datetime.combine(aday.date(), datetime.time(0, 0, 0))
            end = datetime.datetime.combine(aday.date(), datetime.time(23, 59, 59))
            
            
            for project in config['projects']:
            
                try:
                    p = Project.objects.get(slug=project['slug'])
                    self.stdout.write("Fetching data for '{project}' on {date:%Y-%m-%d}\n".format(date=aday, project=p.name))
                
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
                                u = Unit(name=metric['name'], slug=slugify(metric['name']), category=1, period=2)
                                unit_type = metric.get('type', False)
                                if unit_type:
                                    u.observation_unit = unit_type
                                else:
                                    u.observation_unit = UNIT_TYPES[0][0]
                                if verbosity >= 2:
                                    self.stdout.write('Unit "{0}\n"'.format(u.name))
                            self._save_object(u)
                            observation_class = u.observation_type.model_class()
                    
                            (m, m_created) = p.metrics.get_or_create(project=p, unit=u)
                            if verbosity >= 2:
                                self.stdout.write('Metric "{name}" of type "{content_type}" for "{project}"\n'.format(name=u.name, project=p.name, content_type=u.observation_unit))
                        
                            data = acct.get_data(
                                start_date=start.date(),
                                end_date=end.date(),
                                metrics=metric['metrics'],
                                dimensions=metric.get('dimensions', None)
                            )
                            if verbosity >= 2:
                                self.stdout.write("data len is {0}\n".format(len(data)))
                                if len(data):
                                    self.stdout.write("metrics len is {0}\n".format(len(data[0].metrics)))
                            if len(data) == 0:
                                self.stderr.write("No data for '{project}': {metric} on {date:%Y-%m-%d}\n".format(metric=metric['metrics'], date=start, project=p.name)) 
                            else:
                                try:
                                    o = observation_class.objects.get(
                                        metric=m,
                                        from_datetime=start,
                                        to_datetime=end,
                                    )
                                except observation_class.DoesNotExist:
                                    o = observation_class(
                                        metric=m,
                                        from_datetime=start,
                                        to_datetime=end,
                                    )
                                if observation_class is ObjectObservation:
                                    o.value = self._generate_sorted_list(data)
                                else:
                                    o.value = Decimal(data[0].metrics[0].value) # certain data comes back as a float (time on site), so easier to handle as such and let mode convert
                                if verbosity >= 2:
                                    self.stdout.write('Observation for metric "{0}" at "{1}" with value:\n{2}\n'.format(u.name, start, o.value))
                                self._save_object(o)
            
                except Project.DoesNotExist:
                    raise CommandError( "{0} project is not found".format(project['slug']) )