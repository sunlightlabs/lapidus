from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError

from lapidus.metrics.models import Project, Metric, Unit, CountObservation, ObjectObservation, UNIT_TYPES, CATEGORIES, PERIODS

import datetime
import json
from urlparse import urlsplit, urlunsplit
from urllib import urlencode
from urllib2 import urlopen, URLError
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import iso8601

CATEGORY_DICT = {}
for v, k in CATEGORIES:
    CATEGORY_DICT[k] = v    
DEFAULT_CATEGORY = CATEGORY_DICT['web']

PERIOD_DICT = {}
for v, k in PERIODS:
    PERIOD_DICT[k] = v
DEFAULT_PERIOD = PERIOD_DICT['daily']

class Command(BaseCommand):
    help = """Load data from endpoints specified in an ENDPOINTS_CONFIG file."""
    
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
        configfile = options.get('configfile')
        
        if configfile:
            try:
                config = json.load(open(configfile, 'r'))
            except Exception, e:
                raise CommandError( "Couldn't parse configfile '{0}'. Make sure it exists and is the correct format.\n".format(configfile) )
        else:
            config = json.load(open(settings.ENDPOINTS_CONFIG, 'r'))

            for key, value in config.iteritems():
                try:
                    p = Project.objects.get(slug=key)
                    if verbosity >= 2:
                        self.stdout.write("Project: {0}\n".format(p.name))
                    endpoints = value
                
                    for endpt in endpoints:
                        if endpt.get('name', None):
                            endpoint_url = endpt.get('url', None)
                            if not endpoint_url:
                                raise CommandError( "No endpoint url provided for {project} metric '{metric}' in ENDPOINTS_CONFIG file\n".format(project=p.name, metric=endpt['name']) )

                            period_key = endpt.get('period', DEFAULT_PERIOD)
                            if period_key not in PERIOD_DICT:
                                raise CommandError( "period '{0}' not a valid choice\n".format(period_key) )
                            if verbosity >= 2:
                                self.stdout.write("period: {0}\n".format(period_key))
                            
                            if len(args):
                                from_date = iso8601.parse_date(args[0])
                            else:
                                from_date = datetime.datetime.combine(datetime.datetime.now() - datetime.timedelta(1), datetime.time(0, 0, 0))

                            if len(args) > 1:
                                to_date = iso8601.parse_date(args[1])
                                datedelta = to_date - from_date
                            else:
                                to_date = datedelta = None

                            if verbosity >= 2:
                                self.stdout.write("from_date: {0}\n".format(from_date))
                                self.stdout.write("to_date  : {0}\n".format(to_date))

                            dates = [from_date]

                            if datedelta and datedelta.days > 1:
                                dates += [from_date + datetime.timedelta(days=r) for r in range(1, datedelta.days+1)]
                            
                            category_key = endpt.get('category', DEFAULT_CATEGORY)
                            if category_key not in CATEGORY_DICT:
                                raise CommandError( "category '{0}' not a valid choice\n".format(category_key) )
                        
                            period_key = endpt.get('period', DEFAULT_PERIOD)
                            if period_key != 'daily' or period_key not in PERIOD_DICT:
                                raise CommandError( "period '{0}' not a valid choice\n".format(period_key) )
                            
                            try:
                                u = Unit.objects.get(name=endpt['name'])
                            except Unit.DoesNotExist:
                                u = Unit(name=endpt['name'], slug=slugify(endpt['name']), category=CATEGORY_DICT[category_key], period=PERIOD_DICT[period_key])
                                unit_type = endpt.get('type', False)
                                if unit_type:
                                    u.observation_unit = unit_type
                                else:
                                    u.observation_unit = UNIT_TYPES[0][0]
                                if verbosity >= 2:
                                    self.stdout.write('Unit "{0}" of type "{1}"\n'.format(u.name, unit_type))
                                    self.stdout.write('Category: {0}\n'.format( category_key ))
                                    self.stdout.write('Period: {0}\n'.format( period_key ))
                                    
                            self._save_object(u)
                            observation_class = u.observation_type.model_class()

                            (m, m_created) = p.metrics.get_or_create(project=p, unit=u)
                            
                            for aday in dates:
                                start = datetime.datetime.combine(aday.date(), datetime.time(0, 0, 0))
                                end = datetime.datetime.combine(aday.date(), datetime.time(23, 59, 59))
                                url_args = {}
                                date_arg = endpt.get('date_arg', None)
                                if date_arg:
                                    url_args[date_arg] = start.date()
                                params = urlencode(url_args)
                                req_url = "{base_url}?{params}".format(base_url=endpoint_url, params=params)
                                if verbosity >= 2:
                                    self.stdout.write('req_url: {0}\n'.format(req_url))
                                try:
                                    result = json.load(urlopen(req_url))
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
                                        o.value = self._generate_sorted_list(result)
                                    else:
                                        o.value = Decimal(result) # certain data comes back as a float (time on site), so easier to handle as such and let mode convert
                                    if verbosity >= 2:
                                        self.stdout.write('Observation for metric "{0}" at "{1}" with value:\n{2}\n'.format(u.name, start, o.value))
                                    self._save_object(o)
                                except URLError, e:
                                    raise CommandError( "Error retrieving '{url}: {reason}\n".format(url=endpoint_url, reason=e.reason) )
                                
                                self.stdout.write('Metric: {0}\n'.format(endpt['name']))
                        else:
                            raise CommandError( "Endpoint object must have a name key, value pair\n" )
                        
                except Project.DoesNotExist:
                    raise CommandError( "{0} project is not found".format(key) )
