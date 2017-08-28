"""
The setup script is the centre of all activity in building, distributing,
and installing modules using the Distutils. The main purpose of the setup
script is to describe your module distribution to the Distutils, so that
the various commands that operate on your modules do the right thing.
"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

CONFIG = dict(
    name="CatalogProject",
    description="A generic information sorting web application.",
    version="1.0.0.dev",
    url="https://github.com/noelnoche/udacity-fsnd-catalog",
    author="Noel Noche",
    author_email="contact@hellonoel.com",
    packages=["catalog"],
    license="MIT",
    zip_safe=False
)

setup(**CONFIG)
