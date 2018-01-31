import datetime

from django.core.exceptions import ValidationError
from django import forms
from django.db import models
from django.forms.widgets import Select, NumberInput
from django.utils.dates import MONTHS
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from .flexibledate import flexibledate, parse_flexibledate

MONTH_CHOICES = [(0, _('(Month)'))] + [(str(mi), mm) for mi, mm in MONTHS.items()]

class FlexibleDateWidget(forms.MultiWidget):
    """
    A Widget that splits date input into three inputs

    This also serves as an example of a Widget that has more than one HTML
    element and hence implements value_from_datadict.
    """
    template_name = 'flexibledatefield/widgets/flexibledatefield.html'

    def __init__(self, attrs=None, date_format=None, time_format=None):
        year_attrs = dict(attrs or {})
        year_attrs['size'] = 4
        if attrs:
            year_attrs['required'] = attrs.pop('required', None)
        day_attrs = dict(attrs or {})
        day_attrs['size'] = 2
        day_attrs['required'] = False
        month_attrs = dict(attrs or {})
        month_attrs['required'] = False
        widgets = (
            NumberInput(attrs=year_attrs),
            Select(attrs=month_attrs, choices=MONTH_CHOICES),
            NumberInput(attrs=day_attrs),
        )
        self._is_required = False
        super(FlexibleDateWidget, self).__init__(widgets, attrs)

    def get_context(self, name, value, attrs):
        context = super(FlexibleDateWidget, self).get_context(name, value, attrs)
        for widget in context['widget']['subwidgets'][1:]:
            widget['attrs']['required'] = False
        return context

    def decompress(self, value):
        if value:
            value = flexibledate(value)
            return [
                value.year,
                value.get_month(True),
                value.get_day(True)
            ]
        return [None, None, None]


class FlexibleDateFormField(forms.MultiValueField):
    widget = FlexibleDateWidget

    default_error_messages = {
        'invalid_year': _('Enter a valid year.'),
        'invalid_month': _('Enter a valid month.'),
        'invalid_day': _('Enter a valid value for day.'),
    }
#
#     def __init__(self,*args,**kwargs):
#         defaults={}
#         defaults.update(kwargs)
#         min_value = defaults.pop('min_value',None)
#         max_value = defaults.pop('max_value',None)
#         years = defaults.pop('years', None)
#         defaults['widget']=FlexibleDateWidget(years=years, required=kwargs.get('required',True))
#         # these kwargs cause problems for the generic field type
#         super(FlexibleDateFormField, self).__init__(*args, **defaults)

    def __init__(self, input_date_formats=None, input_time_formats=None, *args, **kwargs):
        errors = self.default_error_messages.copy()
        if 'error_messages' in kwargs:
            errors.update(kwargs['error_messages'])
        localize = kwargs.get('localize', False)
        fields = (
            forms.IntegerField(error_messages={'invalid': errors['invalid_year']},
                      localize=localize),
            forms.ChoiceField(error_messages={'invalid': errors['invalid_month']},
                      choices=MONTH_CHOICES, localize=localize, required=False),
            forms.IntegerField(error_messages={'invalid': errors['invalid_day']},
                      localize=localize, required=False),
        )
        super(FlexibleDateFormField, self).__init__(fields, *args, **kwargs)


    def compress(self, data_list):
        if data_list:
            try:
                year, month, day = data_list
            except (ValueError, TypeError):
                raise ValidationError(_("Invalid value for date."))
            try:
                year = int(year)
            except ValueError:
                year = None
            if not year or year in self.empty_values:
                raise ValidationError(self.error_messages['invalid_year'], code='invalid_year')
            if month or day:
                try:
                    month = int(month)
                except (ValueError):
                    month = 0
                if month not in MONTHS:
                    raise ValidationError(self.error_messages['invalid_month'], code='invalid_month')
            if day:
                try:
                    day = int(day)
                    _ = datetime.date(year, month, day)
                except (ValueError):
                    raise ValidationError(self.error_messages['invalid_day'], code='invalid_day')
            result = flexibledate('{0:04d}{1:02d}{2:02d}'.format(year, month, day))
            return result
        return None


class FlexibleDateProxy(flexibledate):

    def __repr__(self):
        return "flexibledate({})".format(self.value)

    @property
    def display(self):
        return str(self)


class FlexibleDateDescriptor(object):
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

    def from_db_value(self, value, expression, connection, context):
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
