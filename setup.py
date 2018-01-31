#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='django-flexibledatefield',
      version='2.0',
      description='A custom field that can store a date with flexible granularity (i.e. only year, year+month, or full date)',
      author='Jordan Reiter',
      author_email='jordanreiter@gmail.com',
      packages=['flexibledatefield'],
      install_requires=['Django>=1.11'],
)
