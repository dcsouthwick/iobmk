###############################################################################
# Copyright 2019-2020 CERN. See the COPYRIGHT file at the top-level directory
# of this distribution. For licensing information, see the COPYING file at
# the top-level directory of this distribution.
###############################################################################

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open("README.md", "r") as readme_file:
    LONG_DESC = readme_file.read()

setup(
    name='hep-benchmark-suite',
    version='2.0.0',
    description="Benchmark Orchestrator Tool to run several benchmarks.",
    author="Benchmarking Working Group",
    author_email="benchmark-suite-wg-devel@cern.ch",
    long_description=LONG_DESC,
    long_description_content_type="text/markdown",
    url="https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite",
    license='GPLv3',
    scripts=['bin/bmkrun', 'bin/bmk_show_metadata'],
    packages=['hepbenchmarksuite', 'hepbenchmarksuite.plugins', 'hepbenchmarksuite.config'],
    package_data={'hepbenchmarksuite': ['config/*.yml']},
    python_requires='~=3.4',
    install_requires=['pyyaml>=5.1', 'importlib-resources', 'stomp.py', 'hep-score @ git+https://gitlab.cern.ch/hep-benchmarks/hep-score.git@qa-v1.0#egg=hep-score']
)
