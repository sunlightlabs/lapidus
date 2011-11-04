from django.template.defaultfilters import stringfilter
from django import template
register = template.Library()

import datetime

@stringfilter
def secondstoduration(value):
    """formats a value in seconds to a time format"""
    td = datetime.timedelta(seconds=round(float(value)))
    return str(td)

register.filter('secondstoduration', secondstoduration)