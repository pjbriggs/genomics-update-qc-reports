genomics-update-qc-reports
==========================

Introduction
------------

Workspace for efforts to update (and improve) the reports generated for
the ``illumina_qc.sh`` scripts in
https://github.com/fls-bioinformatics-core/genomics

Installation
------------

To install from local version do e.g.::

    git clone https://github.com/pjbriggs/genomics-update-qc-reports
    pip install -r genomics-update-qc-reports/requirements.txt
    pip install genomics-update-qc-reports/

Alternatively to install directly from GitHub into a ``virtualenv``
do e.g.::

    virtualenv venv.qcreporter
    . venv.qcreporter/bin/activate
    pip install -r https://raw.githubusercontent.com/pjbriggs/genomics-update-qc-reports/master/requirements.txt
    pip install git+https://github.com/pjbriggs/genomics-update-qc-reports

Known issues
------------

 - The ``Pillow`` dependency may fail to install with an error of the form::

       ValueError: jpeg is required unless explicitly disabled using --disable-jpeg, aborting

   This error is a known problem for Pillow and can be solved by installing
   the required underlying system libraries - see
   https://pillow.readthedocs.org/en/3.0.0/installation.html#linux-installation

Usage
-----

::
    qcreporter2 DIR [DIR...]

where ``DIR`` is an analysis project from ``auto_process.py``.
