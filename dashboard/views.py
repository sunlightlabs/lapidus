from metrics.models import *
from dashboard.models import *
from django.views.generic import ListView
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.db.models import Q, Sum, Avg

import datetime, calendar

import json

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


def _get_dateform(from_datetime, to_datetime):
    return DateRangeForm(initial={'from_datetime': from_datetime, 'to_datetime': to_datetime})


def get_observations(request):
    form = DateRangeForm(request.GET)
    
    if form.is_valid():
        from_datetime = form.cleaned_data.get('from_datetime', None)
        to_datetime = form.cleaned_data.get('to_datetime', None)
        if from_datetime and to_datetime:
            if from_datetime == to_datetime:
                return HttpResponseRedirect("{0}?{1}".format(reverse('get-observations'), "from_datetime={}".format(from_datetime)))
            else:
                return observations_for_daterange(  request, 
                                                    from_year=from_datetime.year, 
                                                    from_month=from_datetime.month, 
                                                    from_day=from_datetime.day,
                                                    to_year=to_datetime.year, 
                                                    to_month=to_datetime.month, 
                                                    to_day=to_datetime.day)
        elif from_datetime:
            return observations_for_day(request, year=from_datetime.year, month=from_datetime.month, day=from_datetime.day)

    return observations_for_day(request)


def observations_for_day(request, year=None, month=None, day=None):
    """View for displaying a set of metric observations across all projects"""
    
    ordered_units = UnitList.objects.get(default=True).ordered()
    
    extra_units = Unit.objects.select_related().filter(category=1).exclude(id__in=[o.id for o in ordered_units])
    
    logger.debug('Requested for {month} {day} {year}'.format(month=month, day=day, year=year))
    
    
    latest_observation = Observation.objects.filter(metric__unit__in=ordered_units).latest('to_datetime')
    latest_datetime = latest_observation.to_datetime
    if not (year and month and day):
        year    = latest_datetime.year
        month   = latest_datetime.month
        day     = latest_datetime.day
        
    from_datetime = datetime.datetime(int(year), int(month), int(day), 0, 0, 0)
    to_datetime = datetime.datetime(int(year), int(month), int(day), 23, 59, 59)
        
    object_list = []
    
    projects = ProjectList.objects.get(default=True).items.all()
    for project in projects:
        project_metrics = Metric.objects.filter(project=project)
        obj = {
            'project': project,
            'observations': [],
            'extra_observations': [],
            'annotations': []
        }
        for ordered_unit in ordered_units:
            logger.debug('unit in unitcol is {unit}'.format(unit=ordered_unit.slug))
            try:
                metric = project_metrics.get(unit=ordered_unit)
                try:
                    proj_obs = metric.related_observations.latest('to_datetime')
                    obj['observations'].append(proj_obs)
                except Exception, e:
                    logger.debug("No observation for {unit}".format(unit=ordered_unit))
                    obj['observations'].append(None)
            except Exception, e:
                obj['observations'].append(None)
        for extra_unit in extra_units:
            try:
                metric = project_metrics.get(unit=extra_unit)
                try:
                    proj_obs = metric.related_observations.latest('to_datetime')
                    obj['extra_observations'].append(proj_obs)
                except Exception, e:
                    logger.debug("No observation for {unit}".format(unit=extra_unit))
                    obj['extra_observations'].append(None)
            except Exception, e:
                obj['extra_observations'].append(None)
        obj['annotations'] = Annotation.objects.filter(project=project).order_by('-timestamp')
        object_list.append(obj)
    
    form = _get_dateform(from_datetime, to_datetime)
    return render(request, "dashboard/project_list.html", dictionary={  'object_list': object_list,
                                                                        'ordered_units': ordered_units,
                                                                        'from_datetime': from_datetime,
                                                                        'to_datetime': to_datetime,
                                                                        'form': form,
                                                                        'latest_datetime': latest_datetime
                                                                      })


def _aggregate_observation_by_class(unit, project, from_datetime, to_datetime):
    logger.debug('unit in unitcol is {unit}'.format(unit=unit.slug))
    try:
        metric = Metric.objects.get(project=project, unit=unit)
    except Exception, e:
        return None
    
    if metric.is_cumulative:
        try:
            latest_obs = metric.related_observations.filter(to_datetime__lte=to_datetime).latest('to_datetime')
            obs_dict = {
                'metric': metric,
                unit.observation_type.model : latest_obs
            }
            return obs_dict
        except Exception, e:
            return None
    else:
        obs_qs = metric.related_observations.filter(from_datetime__gte=from_datetime, to_datetime__lte=to_datetime)
        if not obs_qs:
            return None
        else:
            obs_class = unit.observation_type.model_class()
            if obs_class is CountObservation:
                try:
                    obs_aggregate = obs_qs.aggregate(value=Sum('value'))
                    obs_dict = {
                        'metric': metric,
                        unit.observation_type.model : {
                            'value': obs_aggregate['value']
                        }
                    }
                    return obs_dict
                except Exception, e:
                    logger.debug("No observation for {unit}".format(unit=unit))
                    return None
            elif obs_class is RatioObservation:
                antecedent_aggregate = obs_qs.aggregate(value=Sum('antecedent__value'))
                consequent_aggregate = obs_qs.aggregate(value=Sum('consequent__value'))
                if antecedent_aggregate['value'] and consequent_aggregate['value']:
                    aggregate_value = float(antecedent_aggregate['value'])/float(consequent_aggregate['value'])
                    obs_dict = {
                        'metric': metric,
                        unit.observation_type.model : {
                            'antecedent': obs_qs[0].antecedent,
                            'value': aggregate_value
                        }
                    }
                    return obs_dict
                else:
                    return None
            else:
                return None
    

def observations_for_daterange(request, from_year, from_month, from_day, to_year, to_month, to_day):
    ordered_units = UnitList.objects.get(default=True).ordered()
    latest_observation = Observation.objects.filter(metric__unit__in=ordered_units).latest('to_datetime')
    latest_datetime = latest_observation.to_datetime
    
    extra_units = Unit.objects.all().exclude(id__in=[u.id for u in ordered_units])

    from_datetime = datetime.datetime(int(from_year), int(from_month), int(from_day), 0, 0, 0)
    to_datetime = datetime.datetime(int(to_year), int(to_month), int(to_day), 23, 59, 59)
    
    object_list = []
    
    projects = ProjectList.objects.get(default=True).items.all()
    for project in projects:
        obj = {
            'project': project,
            'observations': [],
            'extra_observations': []
        }
        for ordered_unit in ordered_units:
            obj['observations'].append( _aggregate_observation_by_class(ordered_unit, project, from_datetime, to_datetime) )
        for extra_unit in extra_units:
            obj['extra_observations'].append( _aggregate_observation_by_class(extra_unit, project, from_datetime, to_datetime) )
            
            
        object_list.append(obj)
    
    form = _get_dateform(from_datetime, to_datetime)
    return render(request, "dashboard/project_list.html", dictionary={  'object_list': object_list,
                                                                        'ordered_units': ordered_units,
                                                                        'from_datetime': from_datetime,
                                                                        'to_datetime': to_datetime,
                                                                        'form': form,
                                                                        'latest_datetime': latest_datetime
                                                                      })
