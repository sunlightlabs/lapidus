from metrics.models import *
from dashboard.models import UnitCollection, Unit
from django.views.generic import ListView
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Q, Sum, Avg

import datetime, calendar

import json

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

class ProjectView(ListView):
    model=Project
    context_object_name="project_list"
    template_name="dashboard/project_list.html"
    
def observations_for_day(request, year=None, month=None, day=None):
    """View for displaying a set of metric observations across all projects"""
    
    # if year not month or day: from_datetime(year, 1, 1, 0, 0, 0), to_datetime = from_datetime(year, 12, 31, 23, 59, 59)
    
    ordered_units = UnitCollection.objects.select_related().get(name='Default').ordered_units()
    
    extra_units = Unit.objects.all().exclude(id__in=[o.unit_id for o in ordered_units])
    
    logger.debug('Requested for {month} {day} {year}'.format(month=month, day=day, year=year))
    
    
    if not (year and month and day):
        # TODO make get most recent day out of the ordered units, which may not be yesterday
        latest_observation = Observation.objects.filter(metric__unit__in=ordered_units).latest('to_datetime')
        year    = latest_observation.to_datetime.year
        month   = latest_observation.to_datetime.month
        day     = latest_observation.to_datetime.day
        
    from_datetime = datetime.datetime(int(year), int(month), int(day), 0, 0, 0)
    to_datetime = datetime.datetime(int(year), int(month), int(day), 23, 59, 59)
        
    observations = Observation.objects.select_related().filter(Q(metric__is_cumulative=True) | Q(Q(from_datetime=from_datetime), Q(to_datetime=to_datetime)))
    
    object_list = []
    
    projects = Project.objects.select_related().all()
    for project in projects:
        obj = {
            'project': project,
            'observations': [],
            'extra_observations': []
        }
        project_observations = observations.filter(metric__project=project)
        for ordered_unit in ordered_units:
            logger.debug('unit in unitcol is {unit}'.format(unit=ordered_unit.unit.slug))
            try:
                proj_obs = project_observations.filter(metric__unit=ordered_unit.unit).latest('to_datetime')
                obj['observations'].append(proj_obs)
            except Exception, e:
                logger.debug("No observation for {unit}".format(unit=ordered_unit.unit))
                obj['observations'].append(None)
        for extra_unit in extra_units:
            try:
                proj_obs = project_observations.filter(metric__unit=extra_unit).latest('to_datetime')
                obj['extra_observations'].append(proj_obs)
            except Exception, e:
                logger.debug("No observation for {unit}".format(unit=extra_unit))
                obj['extra_observations'].append(None)
            
        object_list.append(obj)
    
    return render(request, "dashboard/project_list.html", dictionary={  'object_list': object_list,
                                                                        'ordered_units': ordered_units,
                                                                        'from_datetime': from_datetime,
                                                                        'to_datetime': to_datetime
                                                                      })


def _aggregate_observation_by_class(unit, project, from_datetime, to_datetime):
    """docstring for _aggregate_observation_by_class"""
    obs_class = unit.observation_type.model_class()
    logger.debug('unit in unitcol is {unit}'.format(unit=unit.slug))
    if obs_class is CountObservation:
        try:
            obs_qs = obs_class.objects.filter(metric__project=project, metric__unit=unit, from_datetime__gte=from_datetime, to_datetime__lte=to_datetime)
            obs_aggregate = obs_qs.aggregate(value=Sum('value'))
            obs_dict = {
                'metric': obs_qs[0].metric,
                unit.observation_type.model : {
                    'value': obs_aggregate['value']
                }
            }
            return obs_dict
        except Exception, e:
            logger.debug("No observation for {unit}".format(unit=unit))
            return None
    elif obs_class is RatioObservation:
        obs_qs = obs_class.objects.filter(metric__project=project, metric__unit=unit, from_datetime__gte=from_datetime, to_datetime__lte=to_datetime)
        antecedent_aggregate = obs_qs.aggregate(value=Sum('antecedent__value'))
        consequent_aggregate = obs_qs.aggregate(value=Sum('consequent__value'))
        aggregate_value = float(antecedent_aggregate['value'])/float(consequent_aggregate['value'])
        obs_dict = {
            'metric': obs_qs[0].metric,
            unit.observation_type.model : {
                'antecedent': obs_qs[0].antecedent,
                'value': aggregate_value
            }
        }
        return obs_dict
    else:
        return None
    

def observations_for_daterange(request, from_year, from_month, from_day, to_year, to_month, to_day):
    ordered_units = UnitCollection.objects.select_related().get(name='Default').ordered_units()
    
    extra_units = Unit.objects.all().exclude(id__in=[o.unit_id for o in ordered_units])

    from_datetime = datetime.datetime(int(from_year), int(from_month), int(from_day), 0, 0, 0)
    to_datetime = datetime.datetime(int(to_year), int(to_month), int(to_day), 23, 59, 59)
    
    object_list = []
    
    projects = Project.objects.select_related().all()
    for project in projects:
        obj = {
            'project': project,
            'observations': [],
            'extra_observations': []
        }
        for ordered_unit in ordered_units:
            obj['observations'].append( _aggregate_observation_by_class(ordered_unit.unit, project, from_datetime, to_datetime) )
        for extra_unit in extra_units:
            obj['extra_observations'].append( _aggregate_observation_by_class(extra_unit, project, from_datetime, to_datetime) )
            
            
        object_list.append(obj)
    
    return render(request, "dashboard/project_list.html", dictionary={  'object_list': object_list,
                                                                        'ordered_units': ordered_units,
                                                                        'from_datetime': from_datetime,
                                                                        'to_datetime': to_datetime
                                                                      })
