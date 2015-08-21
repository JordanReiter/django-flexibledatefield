#!/usr/bin/env python

from distutils.core import setup

setup(name='django-flexibledatefield',
      version='1.1',
      description='A custom field that can store a date with flexible granularity (i.e. only year, year+month, or full date)',
      author='Jordan Reiter',
      author_email='jordanreiter@gmail.com',
      packages=['flexibledatefield'],
     )
