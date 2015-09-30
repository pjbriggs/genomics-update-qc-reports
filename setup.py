"""
Description

Setup script to install QCReporter

Copyright (C) University of Manchester 2015 Peter Briggs

"""

readme = open('README.rst').read()

# Setup for installation etc
from setuptools import setup
import qcreport
setup(
    name = "QCReporter",
    version = qcreport.get_version(),
    description = "update of QC reporting utilities",
    long_description = readme,
    url = 'https://github.com/pjbriggs/genomics-update-qc-reports',
    maintainer = 'Peter Briggs',
    maintainer_email = 'peter.briggs@manchester.ac.uk',
    packages = ['qcreport',],
    entry_points = { 'console_scripts': [
        'qcreporter2 = qcreport.cli:main',]
    },
    license = 'Artistic License',
    install_requires = ['pillow',
                        'genomics',
                        'auto_process_ngs'],
    test_suite = 'nose.collector',
    tests_require = ['nose'],
    include_package_data=True,
    zip_safe = False
)
