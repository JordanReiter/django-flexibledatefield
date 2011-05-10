import datetime, re

def fix_date_format(s):
    return re.sub(r'\b0+([0-9])', r'\1', s)

def _cmperror(x, y):
    raise TypeError("can't compare '%s' to '%s'" % (
                    type(x).__name__, type(y).__name__))

_MIN_VALUE = 10000000
_MAX_VALUE = 99991231
class flexibledate(object):
    def __init__(self, value):
        try:
            self.value = int(value.strftime('%Y%m%d'))
        except AttributeError:
            self.value = int(value)
        if self.value < _MIN_VALUE or self.value > _MAX_VALUE:
            raise ValueError("Flexible dates must be between the years %d and %d" % ( _MIN_VALUE/10000, _MAX_VALUE/10000 ))
        if int(str(self.value)[4:6]) > 12:
            raise ValueError("Invalid value for flexible date")
        if int(str(self.value)[7:8]) > 0:
            try:
                self.date
            except AttributeError:
                raise ValueError("Invalid value for flexible date")

    def get_date(self):
        try:
            return datetime.datetime.strptime(str(self.value), '%Y%m%d')
        except ValueError:
            raise AttributeError("%s has no attribute 'date'" % type(self).__name__)
    date = property(get_date)
    
    def get_year(self):
        return int(str(self.value)[:4])
    year = property(get_year)
    
    def get_month(self, empty_allowed=False):
        m = int(str(self.value)[4:6])
        if m > 0:
            return m
        else:
            if empty_allowed:
                return None
            raise AttributeError("%s has no attribute 'month'" % type(self).__name__)
    month = property(get_month)

    def get_day(self, empty_allowed=False):
        d = int(str(self.value)[6:8])
        if d > 0:
            return d
        else:
            if empty_allowed:
                return None
            raise AttributeError("%s has no attribute 'day'" % type(self).__name__)
    day = property(get_day)

    def __str__(self):
        try:
            return fix_date_format(datetime.datetime.strftime(self.date, '%b %d, %Y'))
        except AttributeError:
            try:
                return datetime.datetime.strftime(datetime.date(self.year, self.month, 1), '%B %Y')
            except AttributeError:
                return str(self.year)

    def  __repr__(self):
        return "%s(%d)" % (
                           'flexibledate.' + self.__class__.__name__,
                           int(self.value)
                           )

    def __add__(self, other):
        if isinstance(other, flexibledatedelta):
            new_fd = flexibledate(self.value)
            if other.years:
                new_fd.value += (other.years * 10000)
            if other.months:
                try:
                    new_month = new_fd.month
                    new_month += other.months - 1
                    new_year = new_fd.year + (new_month / 12)
                    new_month = (new_month % 12) + 1
                    day = new_fd.get_day(empty_allowed=True)
                    try:
                        datetime.datetime(new_year, new_month, day or 1)
                        new_fd.value = int("%04d%02d%02d" % (new_year, new_month, day or 0))
                    except ValueError:
                        raise ValueError("I can't add %s to %s because it would create an invalid date." % (repr(other), repr(self))) 
                except AttributeError:
                    raise ValueError("You tried to add a flexible date delta with months to a flexible date without months (What is %s + %d months?)" % (self, other.months))
            if other.days:
                try:
                    new_date_value = new_fd.date + datetime.timedelta(days=other.days)
                    new_fd.value = new_date_value.strftime('%Y%m%d')
                except AttributeError:
                    raise ValueError("You tried to add a flexible date delta with days to a flexible date without days (What is %s + %d days?)" % (self, other.days))
        return new_fd

    def __sub__(self, other):
        if isinstance(other, flexibledatedelta):
            return self + -other
        elif isinstance(other, flexibledate):
            other_month = other.get_month(empty_allowed=True)
            other_day = other.get_day(empty_allowed=True)
            diff_years = self.year - other.year
            diff_months = 0
            diff_days = 0
            if other_day and self.get_day(empty_allowed=True):
                diff_days = self.day - other_day
            if other_month and self.get_month(empty_allowed=True):
                diff_months = self.month - other_month
            return flexibledatedelta(diff_years, diff_months, diff_days)
                

    def __eq__(self, other):
        if isinstance(other, flexibledate):
            return self.__cmp(other) == 0
        else:
            return False

    def __ne__(self, other):
        if isinstance(other, flexibledate):
            return self.__cmp(other) != 0
        else:
            return True

    def __le__(self, other):
        if isinstance(other, flexibledate):
            return self.__cmp(other) <= 0
        else:
            _cmperror(self, other)

    def __lt__(self, other):
        if isinstance(other, flexibledate):
            return self.__cmp(other) < 0
        else:
            _cmperror(self, other)

    def __ge__(self, other):
        if isinstance(other, flexibledate):
            return self.__cmp(other) >= 0
        else:
            _cmperror(self, other)

    def __gt__(self, other):
        if isinstance(other, flexibledate):
            return self.__cmp(other) > 0
        else:
            _cmperror(self, other)

    def __cmp(self, other):
        assert isinstance(other, flexibledate)
        return cmp(self.value, other.value)                     


class flexibledatedelta(object):
    def __init__(self, years=0, months=0, days=0):
        self.years = years
        self.months = months
        self.days = days

        
    def __repr__(self):
        if self.days:
            return "%s(%d, %d, %d)" % ('flexibledate.' + self.__class__.__name__,
                                       self.years,
                                       self.months,
                                       self.days
                                       )
        if self.months:
            return "%s(%d, %d)" % ('flexibledate.' + self.__class__.__name__,
                                       self.years,
                                       self.months
                                       )
        return "%s(%d)" % ('flexibledate.' + self.__class__.__name__,
                           self.years
                           )

    def __str__(self):
        if not (self.years or self.months or self.days):
            return "0 years"
        def plural(n):
            return n, abs(n) != 1 and "s" or ""
        s = []
        if self.days:
            s.append("%d day%s" % (plural(self.days)))
        if self.months:
            s.append("%d month%s" % (plural(self.months)))
        if self.years:
            s.append("%d year%s" % (plural(self.years)))
        return ', '.join(s)
    
    def __add__(self, other):
        if isinstance(other, flexibledatedelta):
            return flexibledatedelta(self.years+other.years, 
                                     self.months+other.months, 
                                     self.days+other.days)
        elif isinstance(other, flexibledate):
            return other + self
        
    def __radd__(self, other):
        return self + other

    def __sub__(self, other):
        if isinstance(other, flexibledatedelta):
            return self + -other
        return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, flexibledatedelta):
            return -self + other
        return NotImplemented

    def __neg__(self):
            return flexibledatedelta(-self.years,
                                     -self.months,
                                     -self.days)

    def __eq__(self, other):
        if isinstance(other, flexibledatedelta):
            return self.__cmp(other) == 0
        else:
            return False

    def __ne__(self, other):
        if isinstance(other, flexibledatedelta):
            return self.__cmp(other) != 0
        else:
            return True

    def __le__(self, other):
        if isinstance(other, flexibledatedelta):
            return self.__cmp(other) <= 0
        else:
            _cmperror(self, other)

    def __lt__(self, other):
        if isinstance(other, flexibledatedelta):
            return self.__cmp(other) < 0
        else:
            _cmperror(self, other)

    def __ge__(self, other):
        if isinstance(other, flexibledatedelta):
            return self.__cmp(other) >= 0
        else:
            _cmperror(self, other)

    def __gt__(self, other):
        if isinstance(other, flexibledatedelta):
            return self.__cmp(other) > 0
        else:
            _cmperror(self, other)

    def __cmp__(self, other):
        assert isinstance(other, flexibledatedelta)
        return cmp(self.__getstate(), other.__getstate())

    def __getstate(self):
        return (self.years, self.months, self.days)

    
class flexibledatespan(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __repr__(self):
        return "%s(%s, %s)" % (
                   'flexibledate.' + self.__class__.__name__,
                   repr(self.start),
                   repr(self.end)
                   )

    def __str__(self):
        if not self.end or self.start == self.end:
            return str(self.start)
        end_day = self.end.get_day(empty_allowed=True)
        end_month = self.end.get_month(empty_allowed=True)
        end_year = self.end.year
        start_day = self.start.get_day(empty_allowed=True)
        start_month = self.start.get_month(empty_allowed=True)
        start_year = self.start.year
        start_date = datetime.date(start_year,start_month or 1,start_day or 1)
        end_date = datetime.date(end_year,end_month or 1,end_day or 1)
        if end_day and start_month == end_month:
            return "%s-%s" % (
                fix_date_format(datetime.datetime.strftime(start_date,'%b %d')),
                fix_date_format(datetime.datetime.strftime(end_date,'%d, %Y')).strip(),
            )
        if end_day and start_year == end_year:
            return "%s-%s" % (
                fix_date_format(datetime.datetime.strftime(start_date,'%b %d')),
                fix_date_format(datetime.datetime.strftime(end_date,'%b %d, %Y')),
            )
        if end_day:
            return "%s-%s" % (
                fix_date_format(datetime.datetime.strftime(start_date,'%b %d, %Y')),
                fix_date_format(datetime.datetime.strftime(end_date,'%b %d, %Y')),
            )
        if end_month and start_year == end_year:
            return "%s-%s" % (
                datetime.datetime.strftime(start_date,'%b'),
                datetime.datetime.strftime(end_date,'%b %Y'),
            )
        if end_month:
            return "%s-%s" % (
                datetime.datetime.strftime(start_date,'%b %Y'),
                datetime.datetime.strftime(end_date,'%b %Y'),
            )
        return "%s-%s" % ( start_year, end_year)