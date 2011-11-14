from metrics.models import Project, Metric, Observation
from dashboard.models import UnitCollection, Unit
from django.views.generic import ListView
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Q

import datetime

import json

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

class ProjectView(ListView):
    model=Project
    context_object_name="project_list"
    template_name="dashboard/project_list.html"
    
def dashboard_list(request, year=None, month=None, day=None):
    """View for displaying a set of metric observations across all projects"""
    ordered_units = UnitCollection.objects.select_related().get(name='Default').ordered_units()
    
    extra_units = Unit.objects.all().exclude(id__in=[o.unit_id for o in ordered_units])
        
    if not (year and month and day):
        # TODO make get most recent day out of the ordered units, which may not be yesterday
        latest_observation = Observation.objects.filter(metric__unit__in=ordered_units).latest('to_datetime')
        year    = latest_observation.to_datetime.year
        month   = latest_observation.to_datetime.month
        day     = latest_observation.to_datetime.day
        
    from_datetime = datetime.datetime(year, month, day, 0, 0, 0)
    to_datetime = datetime.datetime(year, month, day, 23, 59, 59)
        
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
    