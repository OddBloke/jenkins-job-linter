Configuration
=============

jenkins-job-linter is configured via an INI-style file passed on the
command-line with the ``--conf`` option.

Global configuration is read from the ``[job_linter]`` section, and
per-linter configuration is read from ``[job_linter:LINTER_NAME]``
sections (with the name of the linter substituted in).  See the
:ref:`linter documentation <linters>` for details of the configuration
options available for each linter.

.. note::
    These sections should happily sit alongside jenkins-job-builder
    configuration, allowing the configuration for the builder and the
    linter to be in the same file.

Global Configuration Options
----------------------------

``disable_linters``
    a comma-separated list of linter names that should be disabled for
    this run of jenkins-job-linter

``only_run``
    a comma-separated list of linter names that should be the only
    linters enabled for this run of jenkins-job-linter
