from django.template.defaultfilters import stringfilter
from django import template
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.utils.encoding import force_unicode
register = template.Library()

import datetime

@stringfilter
def secondstoduration(value):
    """formats a value in seconds to a time format"""
    try:
        input_val = force_unicode(value)
        decvalue = Decimal(input_val)
    except UnicodeEncodeError:
        return u''
    except InvalidOperation:
        return u''
    hours, remainder = divmod(decvalue.to_integral_value(ROUND_HALF_UP), 3600)
    minutes, seconds = divmod(remainder, 60)
    if not hours:
        return "{minutes}m{seconds:02}s".format(minutes=minutes, seconds=seconds)
    return "{hours}h{minutes}m{seconds:02}s".format(hours=hours,minutes=minutes, seconds=seconds)

register.filter('secondstoduration', secondstoduration)

def percentage(value, arg=0):
    """converts a ratio (float) value to a string representing percentage"""
    return "{value:.{precision}%}".format(value=value, precision=int(arg))

register.filter('percentage', percentage)
