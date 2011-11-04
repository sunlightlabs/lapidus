from metrics.models import Project, Metric, Observation
from dashboard.models import UnitCollection
from django.views.generic import ListView
from django.shortcuts import render
from django.http import HttpResponse

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
    
# TODO change args so if no year/mo/day provided, we default to yesterday?
def dashboard_list(request, year=None, month=None, day=None):
    """View for displaying metric observations across all projects"""
    if not (year and month and day):
        yesterday = datetime.datetime.now() - datetime.timedelta(1)
        year = yesterday.year
        month= yesterday.month
        day=yesterday.day
        
    from_datetime = datetime.datetime(year, month, day, 0, 0, 0)
    to_datetime = datetime.datetime(year, month, day, 23, 59, 59)
        
    observations = Observation.objects.filter(from_datetime=from_datetime, to_datetime=to_datetime)
    ordered_units = UnitCollection.objects.get(name='Default').ordered_units()
    
    object_list = []
    
    projects = Project.objects.all()
    for project in projects:
        obj = {
            'project': project,
            'observations': []
        }
        project_observations = observations.filter(metric__project=project)
        for ordered_unit in ordered_units:
            logger.debug('unit in unitcol is {unit}'.format(unit=ordered_unit.unit.slug))
            obj['observations'].append(project_observations.get(metric__unit=ordered_unit.unit))
        object_list.append(obj)

    return render(request, "dashboard/project_list.html", dictionary={  'object_list': object_list,
                                                                        'ordered_units': ordered_units,
                                                                        'from_datetime': from_datetime,
                                                                        'to_datetime': to_datetime
                                                                      })
    