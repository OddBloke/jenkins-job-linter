# jenkins-job-linter

[![Build Status](https://travis-ci.org/OddBloke/jenkins-job-linter.svg?branch=master)](https://travis-ci.org/OddBloke/jenkins-job-linter)
[![codecov](https://codecov.io/gh/OddBloke/jenkins-job-linter/branch/master/graph/badge.svg)](https://codecov.io/gh/OddBloke/jenkins-job-linter)
[![Requirements Status](https://requires.io/github/OddBloke/jenkins-job-linter/requirements.svg?branch=master)](https://requires.io/github/OddBloke/jenkins-job-linter/requirements/?branch=master)
[![Documentation Status](https://readthedocs.org/projects/jenkins-job-linter/badge/?version=latest)](http://jenkins-job-linter.readthedocs.io/en/latest/?badge=latest)
[![Code Climate](https://codeclimate.com/github/OddBloke/jenkins-job-linter/badges/gpa.svg)](https://codeclimate.com/github/OddBloke/jenkins-job-linter)

Perform linting checks against Jenkins Job Builder XML

## Getting Started

```sh
virtualenv -p $(which python3) jjl
. ./jjl/bin/activate
pip install jenkins-job-linter
jenkins-jobs lint path/to/my/job/builder/definitions
```

## Documentation

See http://jenkins-job-linter.readthedocs.io/en/latest/ for the latest documentation.
