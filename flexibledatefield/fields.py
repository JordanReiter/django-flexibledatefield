import datetime

from django.core.exceptions import ValidationError
from django import forms
from django.db import models
from django.forms.widgets import Select
from django.utils.dates import MONTHS
from django.utils.safestring import mark_safe

from .flexibledate import flexibledate, parse_flexibledate


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

    def render(self, name, value, attrs=None, renderer=None):
        try:
            year_val, month_val, day_val = value.get_year(), value.get_month(empty_allowed=True), value.get_day(empty_allowed=True)
        except AttributeError:
            year_val, month_val, day_val = None, None, None

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
        select_html = s.render(self.year_field % name, year_val, local_attrs, renderer)
        output.append(select_html)

        month_choices = list(MONTHS.items())
        month_choices.append(self.none_value)
        month_choices.sort()
        local_attrs['id'] = self.month_field % id_

        s = Select(choices=month_choices)
        select_html = s.render(self.month_field % name, month_val, local_attrs, renderer)
        output.append(select_html)


        day_choices = [(i, i) for i in range(1, 32)]
        day_choices.insert(0, self.none_value)
        local_attrs['id'] = self.day_field % id_

        s = Select(choices=day_choices)
        select_html = s.render(self.day_field % name, day_val, local_attrs, renderer)
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
            return flexibledate('%04d%02d%02d' % (y, m or 0, d or 0))
        return data.get(name, None)



class FlexibleDateFormField(forms.Field):
    def __init__(self,*args,**kwargs):
        defaults={}
        defaults.update(kwargs)
        min_value = defaults.pop('min_value',None)
        max_value = defaults.pop('max_value',None)
        years = defaults.pop('years', None)
        defaults['widget']=FlexibleDateWidget(years=years, required=kwargs.get('required',True))
        # these kwargs cause problems for the generic field type
        super(FlexibleDateFormField, self).__init__(*args, **defaults)



class FlexibleDateProxy(flexibledate):

    def __repr__(self):
        return "flexibledate({})".format(self.value)

    @property
    def display(self):
        return str(self)


class FlexibleDateDescriptor(object):
    """
    A descriptor for flexible date fields on a model instance.

        >>> instance.flexibledate.value
        20100400

        >>> instance.flexibledate.display
        April 2010
    """
    def __init__(self, field_name, proxy_class):
        self.field_name = field_name
        self.proxy_class = proxy_class

    def __get__(self, instance=None, owner=None):
        # grab the original value before we proxy
        value = instance.__dict__[self.field_name]
        if value is None:
            # We can't proxy a None through a unicode sub-class
            return value
        return self.proxy_class.parse(value)

    def __set__(self, instance, value):
        instance.__dict__[self.field_name] = value


class FlexibleDateField(models.PositiveIntegerField):

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        return flexibledate.parse(value)

    def contribute_to_class(self, cls, name):
        super(FlexibleDateField, self).contribute_to_class(cls, name)
        # Add our descriptor to this field in place of of the normal attribute
        setattr(cls, self.name,
                FlexibleDateDescriptor(self.name, FlexibleDateProxy) )


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
        if not value:
            return None

        if isinstance(value, flexibledate):
            return value

        try:
            return flexibledate.parse(value)
        except (ValueError, TypeError) as err:
            raise ValidationError(err)

    def get_prep_value(self, value):
        if not value:
            return None
        return int(self.to_python(value))

    def get_db_prep_lookup(self, lookup_type, value, connection, prepared=False):
        if isinstance(value, flexibledate):
            value = value.value
        elif isinstance(value, (list, tuple)):
            value = [self.get_prep_value(vv) for vv in value]
        else:
            try:
                value = int(value.strftime('%Y%m%d'))
            except AttributeError:
                value = int(value)
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
