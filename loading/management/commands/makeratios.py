from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q
# from django.contrib.contenttypes.models import ContentType
from googleanalytics import Connection
from lapidus.metrics.models import Project, Metric, Unit, CountObservation, RatioObservation, UNIT_TYPES, CATEGORIES, PERIODS
# import datetime
import json

# Unit.name, slug, category, period, observation_type, observation_unit (UNIT_TYPES)
RATIO_DEFAULTS = {
    'category': 'web',
    'period': 'daily',
    'type': 'ratio'
}

period_id, period_name = zip(*PERIODS)
category_id, category_name = zip(*CATEGORIES)


class Command(BaseCommand):
    help = """Make RatioObservations from CountObservations"""

    # run validation/cleaning on object before attempting to save
    def _save_object(self, obj):
        try:
            obj.full_clean()
        except ValidationError, e:
            raise CommandError("[%s]:\n\t%s" % (obj, ', '.join(e.messages)))
        try:
            obj.save()
        except IntegrityError, e:
            raise CommandError("[%s]:\n\t%s" % (obj, ','.join(e.messages)))

    def _make_missing_metrics(self, u):
        """Make metrics for Projects that don't have one for a particular unit"""
        applicable_projs = Project.objects.exclude(metrics__unit=u)
        for proj in applicable_projs:
            m = Metric.objects.create(project=proj, unit=u)
        

    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity'))

        if verbosity >= 2:
            self.stdout.write('makeratios load: {fp}\n'.format(fp=settings.RATIOS_CONFIG))
        config = json.load(open(settings.RATIOS_CONFIG))
        if verbosity >= 2:
            self.stdout.write('makeratios config: {config}\n'.format(config=config))
        
        
        for ratio in config:
            pdkey = ratio.get("period", RATIO_DEFAULTS["period"])
            ctkey = ratio.get("category", RATIO_DEFAULTS["category"])
            (u, u_created) = Unit.objects.get_or_create( name=ratio["name"],
                                            slug=slugify(ratio["name"]), 
                                            period= period_id[period_name.index(pdkey)],
                                            category= category_id[category_name.index(ctkey)],
                                            observation_unit=ratio.get("type", "ratio")
                                            )
            self._make_missing_metrics(u)
            # generate ratioobservations for every project and antecedent/consequent that doesn't have one
            all_projects = Project.objects.select_related().all()
            for project in all_projects:
                try:
                    antecedent_metric = Metric.objects.get(project=project, unit__slug=ratio['antecedent'])
                except Metric.DoesNotExist:
                    msg = 'antecedent metric "{metric}" does not exist for {project}\n'.format(metric=ratio['antecedent'], project=project)
                    self.stderr.write(msg)
                try:
                    consequent_metric = Metric.objects.get(project=project, unit__slug=ratio['consequent'])
                except Metric.DoesNotExist:
                    msg = 'consequent metric "{metric}" does not exist for {project}\n'.format(metric=ratio['consequent'], project=project)
                    self.stderr.write(msg)
                ratio_metric = Metric.objects.get(project=project, unit=u) # We already searched for it then created it
                antecedent_class = antecedent_metric.unit.observation_type.model_class()
                consequent_class = consequent_metric.unit.observation_type.model_class()
                
                antecedent_observations = antecedent_class.objects.filter(metric=antecedent_metric).order_by('from_datetime', 'to_datetime')
                consequent_observations = consequent_class.objects.filter(metric=consequent_metric).order_by('from_datetime', 'to_datetime')
                # FIXME This doesn't calculate new ratioobservations for each time frame...
                for a_obs in antecedent_observations:
                    if verbosity >= 2:
                        msg = '{project}\'s "{a_unit}" for {from_dt:%Y-%m-%d %H:%M:%S} - {to_dt:%Y-%m-%d %H:%M:%S} \n'.format(a_unit=a_obs.metric.unit.name, 
                                                                                                            project=project, 
                                                                                                            from_dt=a_obs.from_datetime, 
                                                                                                            to_dt=a_obs.to_datetime)
                        self.stderr.write(msg)
                    c_obs = consequent_observations.get(from_datetime=a_obs.from_datetime, to_datetime=a_obs.to_datetime)
                    (r, new_r) = RatioObservation.objects.get_or_create(
                        metric=ratio_metric,
                        antecedent=a_obs,
                        consequent=c_obs,
                        from_datetime=a_obs.from_datetime, 
                        to_datetime=a_obs.to_datetime
                    )
                    if verbosity >= 2:
                        msg = 'Ratio observation for {a_unit_name}/{c_unit_name}\n'.format(a_unit_name=a_obs.metric.unit.name, c_unit_name=c_obs.metric.unit.name)
                        self.stdout.write(msg)