from django import template
from django.template.defaultfilters import date as django_date_filter
import re, datetime

register = template.Library()

def flexibledateformat(value, arg=None):
    RE_DATE = re.compile(r'(\d{4})(\d\d)(\d\d)$')
    try:
        value = str(int(value))
    except:
        return None
    match = RE_DATE.match(str(value))
    if match:
        year_val, month_val, day_val = [int(v) for v in match.groups()]
    else:
        raise ValueError("Invalid value for flexible date: %s" % value)
    if day_val:
        return django_date_filter(datetime.date(year_val,month_val,day_val),'M j, Y')
    elif month_val:
        return django_date_filter(datetime.date(year_val,month_val,1),'F Y')
    else:
        return year_val
register.filter('flexibledateformat', flexibledateformat)
