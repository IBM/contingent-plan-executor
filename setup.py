"""
hovor-exec for Bluemix
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='hovor-exec',
    version='0.0.1',
    description='Execution monitor for dialogue plans',
    long_description=long_description,
    url='https://github.ibm.com/conversation-research/hovor-exec',
    license='Apache-2.0'
)
