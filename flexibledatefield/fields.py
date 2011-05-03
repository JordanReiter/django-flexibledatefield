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

from flexibledate import flexibledate

from django import forms

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
        year_val, month_val, day_val = value.get_year(), value.get_month(empty_allowed=True), value.get_day(empty_allowed=True)

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
    __metaclass__ = models.SubfieldBase
    
    def get_internal_type(self):
        return 'IntegerField'

    def __init__(self, *args, **kwargs):
        self.years = kwargs.pop('years',None)
        super(FlexibleDateField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        """
        Validates that the input can be converted to a date. 
        Returns a flexibledate object.
        """
        try:
            return flexibledate(value)
        except ValueError, inst:
            raise ValidationError(inst)
        
    def get_prep_value(self, value):
        try:
            value = value.value
        except:
            pass
        return value

    def get_db_prep_lookup(self, lookup_type, value, connection, prepared=False):
        if isinstance(value, flexibledate):
            value = value.value
        if not prepared:
            value = self.get_prep_lookup(lookup_type, value)
        if lookup_type == 'year':
            return (int("%d0000" % value), int("%d1231" % value))
        else:
            return super(FlexibleDateField, self).get_db_prep_lookup(lookup_type, value, connection=connection, prepared=prepared)

    def formfield(self, *args, **kwargs):
        defaults={'form_class': FlexibleDateFormField}
        defaults.update(kwargs)
        return super(FlexibleDateField, self).formfield(years=self.years, *args, **defaults)
