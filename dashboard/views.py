from metrics.models import *
from dashboard.models import *
from dashboard.forms import *
from django.views.generic import ListView
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseNotAllowed
from django.core.urlresolvers import reverse
from django.db.models import Q, Sum, Avg

import datetime, calendar

import json

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

CATEGORY_DICT = { v: k for k,v in CATEGORIES }

def _get_dateform(from_datetime, to_datetime):
    return DateRangeForm(initial={'from_datetime': from_datetime, 'to_datetime': to_datetime})

def _get_projects_in_category(category_id):
    """Retrieve all projects that have a web metric"""
    projects = Project.objects.all()
    cat_metrics_ids = [wm.id for wm in Metric.objects.filter(unit__category=category_id) if wm.related_observations.count() != 0]
    return [ p for p in projects if Metric.objects.filter(project=p, id__in=cat_metrics_ids).exists() ]

def get_observations(request, category='web', project=None):
    form = DateRangeForm(request.GET)
    annotation_form = None
    ordered_units = UnitList.objects.get(default_for=CATEGORY_DICT[category]).ordered()
    latest_observation = Observation.objects.filter(metric__unit__in=ordered_units, metric__is_cumulative=False).latest('to_datetime')
    latest_datetime = latest_observation.to_datetime
    
    extra_units = Unit.objects.select_related().filter(category=CATEGORY_DICT[category]).exclude(id__in=[u.id for u in ordered_units])
    
    if project:
        projects = [Project.objects.get(slug=project)]
    else:
        projects = _get_projects_in_category(CATEGORY_DICT[category])
    
    if form.is_valid():
        raw_from_date = form.cleaned_data.get('from_datetime', None)
        from_datetime = datetime.datetime.combine(raw_from_date, datetime.time(0, 0, 0))
        raw_to_date = form.cleaned_data.get('to_datetime', None)
        to_datetime = datetime.datetime.combine(raw_to_date,  datetime.time(23, 59, 59)) if raw_to_date else raw_to_date
        if from_datetime and to_datetime:
            if from_datetime.date() == to_datetime.date():
                return HttpResponseRedirect("{0}?{1}".format(reverse('get-observations'), "from_datetime={}".format(from_datetime.date())))
            else:
                object_list, from_datetime, to_datetime = observations_for_daterange(   projects, 
                                                                                        ordered_units, 
                                                                                        extra_units, 
                                                                                        from_datetime,
                                                                                        to_datetime )
        elif from_datetime:
            object_list, from_datetime, to_datetime = observations_for_day(projects, ordered_units, extra_units, from_datetime)
    else:
        object_list, from_datetime, to_datetime = observations_for_day(projects, ordered_units, extra_units, latest_datetime)
    form = _get_dateform(from_datetime, to_datetime)
    if project:
        template = "dashboard/project_detail.html"
        annotation_form = AnnotationForm(instance=Annotation(project=projects[0], timestamp=to_datetime))
    else:
        template = "dashboard/project_list.html"
    
    
    return render(request, template, dictionary= { 'object_list': object_list,
                                                   'ordered_units': ordered_units,
                                                   'from_datetime': from_datetime,
                                                   'to_datetime': to_datetime,
                                                   'form': form,
                                                   'latest_datetime': latest_datetime,
                                                   'categories': CATEGORIES,
                                                   'annotation_form': annotation_form
                                                })
    


def observations_for_day(projects, ordered_units, extra_units, day_datetime):
    """View for displaying a set of metric observations across all projects"""
    
    logger.debug('Requested for {month} {day} {year}'.format(month=day_datetime.month, day=day_datetime.day, year=day_datetime.year))
    from_datetime = day_datetime
    to_datetime = datetime.datetime(int(day_datetime.year), int(day_datetime.month), int(day_datetime.day), 23, 59, 59)
        
    object_list = []
    
    for project in projects:
        obj = {
            'project': project,
            'observations': [],
            'extra_observations': [],
            'annotations': []
        }
        for ordered_unit in ordered_units:
            logger.debug('unit in unitcol is {unit}'.format(unit=ordered_unit.slug))
            try:
                metric = Metric.objects.get(project=project, unit=ordered_unit)
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
                metric = Metric.objects.get(project=project, unit=extra_unit)
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
    
    return (object_list, from_datetime, to_datetime)


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
                        },
                        'observations': obs_qs
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
                        },
                        'observations': obs_qs
                    }
                    return obs_dict
                else:
                    return None
            else:
                obs_dict = {
                    'metric': metric,
                    'observations': obs_qs
                }
                return obs_dict
    

def observations_for_daterange(projects, ordered_units, extra_units, from_datetime, to_datetime):
    object_list = []
    
    for project in projects:
        obj = {
            'project': project,
            'observations': [],
            'extra_observations': [],
            'annotations': []
        }
        for ordered_unit in ordered_units:
            obj['observations'].append( _aggregate_observation_by_class(ordered_unit, project, from_datetime, to_datetime) )
        for extra_unit in extra_units:
            obj['extra_observations'].append( _aggregate_observation_by_class(extra_unit, project, from_datetime, to_datetime) )
        obj['annotations'] = Annotation.objects.filter(project=project).order_by('-timestamp')
            
        object_list.append(obj)
    
    return (object_list, from_datetime, to_datetime)

def add_annotation(request):
    # import ipdb; ipdb.set_trace()
    if request.method == "POST":
        form = AnnotationForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse('Annotation Saved', mimetype="text/plain")
        else:
            return HttpResponse('Form Invalid', mimetype="text/plain")
    else:
        return HttpResponseNotAllowed([['POST',]])
        
          