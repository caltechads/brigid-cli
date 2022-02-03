#!/usr/bin/env python
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="brigid-cli",
    version='0.1.0',
    description="Command line client for Caltech ADS Brigid",
    url="https://bitbucket.org/caltech-imss-ads/brigid/",
    author="Caltech IMSS ADS",
    author_email="imss-ads-staff@caltech.edu",
    packages=find_packages(exclude=["*.test", "*.test.*", "test.*", "test", "bin", "*.pyc"]),
    include_package_data=True,
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=['devops'],
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    entry_points={
        'console_scripts': ['brigid = brigid_cli.main:main']
    },
    install_requires=[
        "click >= 7.1.2",
        "pydantic >= 1.7.3",
        "tabulate >= 0.8.7",
        "PyYAML >= 5.1.2",
        "brigid_api_client @ git+http://github.com/caltechads/brigid-api-client@master#egg=brigid-api-client"
    ],
)
