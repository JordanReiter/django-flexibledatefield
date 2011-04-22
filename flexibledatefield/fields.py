"""
    widgets.py
"""
import datetime
import re

from django.core.exceptions import ValidationError
from django.core import validators
from django import forms
from django.db import models
from django.forms.widgets import Select, TextInput
from django.utils.dates import MONTHS
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

MIN_VALUE = 18000000
MAX_VALUE = 21000000
RE_DATE = re.compile(r'(\d{4})(\d\d)(\d\d)$')

def flexibledatecompare(f, o):
    try:
        fd = datetime.datetime.strftime(f, '%Y%m%d')
    except TypeError:
        fd = f
    try:
        od = datetime.datetime.strftime(o, '%Y%m%d')
    except TypeError:
        od = o
    fmatch = RE_DATE.match(str(fd))
    omatch = RE_DATE.match(str(od))
    if not fmatch or not omatch:
        raise TypeError("Invalid format for one of the dates.")
    if fmatch:
        fyear, fmonth, fday = [int(v) for v in fmatch.groups()]
    if omatch:
        oyear, omonth, oday = [int(v) for v in omatch.groups()]
    if fyear != oyear:
        return fyear-oyear
    if fmonth == omonth:
        if fday and oday:
            return fday-oday
        return 0
    else:
        if fmonth and omonth:
            return fmonth-omonth
        else:
            return 0

def flexibledatelt(fd,d):
    return flexibledatecompare(fd,d) < 0

def flexibledategt(fd,d):
    return flexibledatecompare(fd,d) > 0

def flexibledateeq(fd,d):
    return flexibledatecompare(fd,d) == 0
        

def flexibledatespan(start, end):
    if not end or start == end:
        return start.display
    smatch = RE_DATE.match(str(start))
    ematch = RE_DATE.match(str(end))
    if smatch:
        syear, smonth, sday = [int(v) for v in smatch.groups()]
    if ematch:
        eyear, emonth, eday = [int(v) for v in ematch.groups()]
    sdate = datetime.date(syear,smonth or 1,sday or 1)
    edate = datetime.date(eyear,emonth or 1,eday or 1)
    if eday and smonth == emonth:
        return "%s-%s" % (
            datetime.datetime.strftime(sdate,'%b %e'),
            datetime.datetime.strftime(edate,'%e, %Y').strip(),
        )
    if eday and smonth != emonth:
        return "%s-%s" % (
            datetime.datetime.strftime(sdate,'%b %e'),
            datetime.datetime.strftime(edate,'%b %e, %Y'),
        )
    elif eday:
        return "%s-%s" % (
            datetime.datetime.strftime(sdate,'%b %e, %Y'),
            datetime.datetime.strftime(edate,'%b %e, %Y'),
        )
    else:
        return "%s-%s" % (
            datetime.datetime.strftime(sdate,'%b %Y'),
            datetime.datetime.strftime(edate,'%b %Y'),
        )

def flexibledateformat(value):
    try:
        value = str(int(value))
    except:
        return None
    try:
        match = RE_DATE.match(str(value))
        if match:
            year_val, month_val, day_val = [int(v) for v in match.groups()]
        if day_val:
            return datetime.datetime.strftime(datetime.date(year_val,month_val,day_val),'%b %e, %Y')
        elif month_val:
            return datetime.datetime.strftime(datetime.date(year_val,month_val,1),'%B %Y')
        else:
            return str(year_val)
    except:
        return None

class FlexibleDateWidget(forms.Widget):
    """
    A Widget that splits date input into three inputs

    This also serves as an example of a Widget that has more than one HTML
    element and hence implements value_from_datadict.
    """
    none_value = (0, '(optional)')
    month_field = '%s_month'
    day_field = '%s_day'
    year_field = '%s_year'

    def __init__(self, attrs=None, years=None, required=True):
        # years is an optional list/tuple of years to use in the "year" select box.
        self.attrs = attrs or {}
        self.required = required
        if years:
            self.years = years
        else:
            this_year = datetime.date.today().year
            self.years = range(this_year-10, this_year+11)

    def render(self, name, value, attrs=None):
        try:
            year_val, month_val, day_val = value.year, value.month, value.day
        except AttributeError:
            year_val = month_val = day_val = None
            try:
                value = int(value)
                try:
                    match = RE_DATE.match(str(value))
                    if match:
                        year_val, month_val, day_val = [int(v) for v in match.groups()]
                except TypeError, inst:
                    raise Exception("%s" % inst)
            except: 
                pass

        output = []

        if 'id' in self.attrs:
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name
                        
        local_attrs = self.build_attrs(id=self.year_field % id_)
        year_choices = [(i, i) for i in self.years]
        year_choices.reverse()
        if not self.required:
            year_choices = [(0,'(year)')] + year_choices
        s = Select(choices=year_choices)
        select_html = s.render(self.year_field % name, year_val, local_attrs)
        output.append(select_html)

        month_choices = MONTHS.items()
        month_choices.append(self.none_value)
        month_choices.sort()
        local_attrs['id'] = self.month_field % id_
        
        s = Select(choices=month_choices)
        select_html = s.render(self.month_field % name, month_val, local_attrs)
        output.append(select_html)

        
        day_choices = [(i, i) for i in range(1, 32)]
        day_choices.insert(0, self.none_value)
        local_attrs['id'] = self.day_field % id_
        
        s = Select(choices=day_choices)
        select_html = s.render(self.day_field % name, day_val, local_attrs)
        output.append(select_html)

        return mark_safe(u'\n'.join(output))

    def id_for_label(self, id_):
        return '%s_year' % id_
    id_for_label = classmethod(id_for_label)

    def value_from_datadict(self, data, files, name):
        try:
            y = int(data.get(self.year_field % name))
        except:
            y = 0
        try:
            m = int(data.get(self.month_field % name))
        except:
            m = 0
        try:
            d = int(data.get(self.day_field % name))
        except:
            d = 0
        if y == m == d == "0":
            return None
        if y:
            return '%04d%02d%02d' % (y, m or 0, d or 0)
        return data.get(name, None)
        

class FlexibleDateFormField(forms.Field):
    def __init__(self,*args,**kwargs):
        defaults={}
        defaults.update(kwargs)
        min_value = defaults.pop('min_value',None)
        max_value = defaults.pop('max_value',None)
        years = defaults.pop('years',None)
        defaults['widget']=FlexibleDateWidget(years=years, required=kwargs.get('required',True))
        # these kwargs cause problems for the generic field type
        super(FlexibleDateFormField, self).__init__(*args, **defaults)

class FlexibleDateDescriptor(object):
    """
    A descriptor for flexible date fields on a model instance. 

        >>> instance.flexibledate.value
        20100400
        
        >>> instance.flexibledate.display
        April 2010
    """
    def __init__(self, field):
        self.field = field

    def __get__(self, instance=None, owner=None):
        if instance is None:
            raise AttributeError(
                "The '%s' attribute can only be accessed from %s instances."
                % (self.field.name, owner.__name__))
        class result(int):
            def __init__(self,value,*args,**kwargs):
                self.display = flexibledateformat(value)
                super(result,self).__init__(*args,**kwargs)
        try:
            return result(instance.__dict__[self.field.name])
        except TypeError:
            return None

    def __set__(self, instance, value):
        try:
            instance.__dict__[self.field.name] = int(value)
        except:
            instance.__dict__[self.field.name] = None


class FlexibleDateField(models.PositiveIntegerField):

    descriptor_class = FlexibleDateDescriptor

    default_error_messages = {
        'invalid': _(u'Something else'),
        'bad_year': _(u'Enter a valid year (between %(min)s-%(max)s).' % {'min':str(MIN_VALUE)[:4],'max':str(MAX_VALUE)[:4]}),
        'day_no_month': _(u'You entered a day but not a month.'),
        'month_no_year': _(u'You entered a month but no year.'),
        'bad_date': _(u'You entered an invalid date.'),
    }

    def get_internal_type(self):
        return 'IntegerField'

    def __init__(self, *args, **kwargs):
        self.years = kwargs.pop('years',None)
        super(FlexibleDateField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        """
        Validates that the input can be converted to a date. Returns a Python
        datetime.date object.
        """
        if value in validators.EMPTY_VALUES:
            return None
        try:
            value = int(value)
        except ValueError:
            raise ValidationError(self.error_messages['invalid'])
        match = RE_DATE.match(str(value))
        if match:
            year_val, month_val, day_val = [int(v) for v in match.groups()]
        if day_val and not month_val:
            raise ValidationError(self.error_messages['day_no_month'])
        if month_val and not year_val:
            raise ValidationError(self.error_messages['month_no_year'])
        if value < MIN_VALUE or value > MAX_VALUE:
            raise ValidationError(self.error_messages['bad_year'])
        test_day = day_val or 1
        test_month = month_val or 1
        try:
            d = datetime.datetime(year_val,month_val or test_month,day_val or test_day)
        except ValueError:
            raise ValidationError(self.error_messages['bad_date'])
        return value

    def get_db_prep_lookup(self, lookup_type, value, connection, prepared=False):
        if not prepared:
            value = self.get_prep_lookup(lookup_type, value)
        if lookup_type == 'year':
            return (int("%d0000" % value), int("%d1231" % value))
        else:
            return super(FlexibleDateField, self).get_db_prep_lookup(lookup_type, value, connection, prepared)
        


    def contribute_to_class(self, cls, name):
        super(FlexibleDateField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, self.descriptor_class(self))

    def formfield(self, *args, **kwargs):
        defaults={'form_class': FlexibleDateFormField}
        defaults.update(kwargs)
        return super(FlexibleDateField, self).formfield(years=self.years, *args, **defaults)
