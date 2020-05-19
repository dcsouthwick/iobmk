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
    author_email="@cern.ch",
    long_description=LONG_DESC,
    long_description_content_type="text/markdown",
    url="https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite",
    license='GPLv3',
    scripts=['bin/bmkrun', 'bin/show_metadata'],
    packages=['hepbenchmarksuite', 'hepbenchmarksuite.plugins']
)
