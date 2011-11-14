from django.template.defaultfilters import stringfilter
from django import template
register = template.Library()

import datetime

@stringfilter
def secondstoduration(value):
    """formats a value in seconds to a time format"""
    # td = datetime.timedelta(seconds=round(float(value)))
    hours, remainder = divmod(int(round(float(value))), 3600)
    minutes, seconds = divmod(remainder, 60)
    if not hours:
        return "{minutes}m{seconds:02}s".format(minutes=minutes, seconds=seconds)
    return "{hours}h{minutes}m{seconds:02}s".format(hours=hours,minutes=minutes, seconds=seconds)

register.filter('secondstoduration', secondstoduration)

def percentage(value, arg=0):
    """converts a ratio (float) value to a string representing percentage"""
    return "{value:.{precision}%}".format(value=value, precision=int(arg))

register.filter('percentage', percentage)
