###############################################################################
# Copyright 2019-2020 CERN. See the COPYRIGHT file at the top-level directory
# of this distribution. For licensing information, see the COPYING file at
# the top-level directory of this distribution.
###############################################################################

import os
import json
import logging
import time

from hepbenchmarksuite import db12
from hepbenchmarksuite import utils

_log = logging.getLogger(__name__)


class HepBenchmarkSuite(object):
    """********************************************************
                  *** HEP-BENCHMARK-SUITE ***
     *********************************************************"""

    RESULT_FILES = {
        'hs06_32' : 'HS06/hs06_32_result.json',
        'hs06_64' : 'HS06/hs06_64_result.json',
        'spec2017': 'SPEC2017/spec2017_result.json',
        'hepscore': 'HEPSCORE/hepscore_result.json',
        'db12'    : 'db12_result.json',
    }

    def __init__(self,  config=None):
        """Initialize setup"""
        self._bench_queue = config['global']['benchmarks']
        self.selected_benchmarks = config['global']['benchmarks'].copy()
        self._config = config['global']
        self._config_full = config
        self._extra = {}

    def start(self):
        _log.info("Starting benchmark suite")

        self._extra['start_time'] = time.strftime(
            '%Y-%m-%dT%H:%M:%SZ', time.gmtime())

        if self._preflight() == 0:
            _log.info("Pre-flight checks passed successfully.")
            self.run()
        else:
            _log.error("Pre-flight checks failed.")

    def _preflight(self):
        """Perform pre-flight checks."""

        _log.info("Running pre-flight checks")
        checks = []

        _log.info(" - Checking provided work dirs exist...")
        os.makedirs(self._config['rundir'], exist_ok=True)
        os.makedirs(self._config_full['hepspec06']['hepspec_volume'], exist_ok=True)

        _log.info(" - Performing configuration validation...")
        for bench in self.selected_benchmarks:
            if bench in ['hs06_32', 'hs06_64', 'spec2017']:
                checks.append(utils.validate_hs06(self._config_full))

        # Check if any pre-flight check failed
        if any(checks):
            return 1
        else:
            return 0

    def run(self):

        # Check if there are still benchmarks to run
        if len(self._bench_queue) == 0:
            self._extra['end_time'] = time.strftime(
                '%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            self.cleanup()

        else:
            _log.info("Benchmarks left to run: {}".format(self._bench_queue))
            bench2run = self.dequeue()
            _log.info("Running benchmark: {}".format(bench2run))
            

            if bench2run == 'db12':
                returncode = db12.run_db12(rundir=self._config['rundir'], cpu_num=2)

            elif bench2run == 'hepscore':
                returncode = utils.run_hepscore(conf=self._config_full, bench=bench2run)

            elif bench2run in ['hs06_32', 'hs06_64', 'spec2017']:
                returncode = utils.run_hepspec(conf=self._config_full, bench=bench2run)

            self.check_lock()
            
            return returncode
        

    def dequeue(self):
        return self._bench_queue.pop(0)

    def check_lock(self):
        # TODO: Check lock files
        # loop until lock is released from benchmark
        # print(os.path.exists("bench.lock"))
        # Release lock and resume benchmarks
        self.run()

    def cleanup(self):
        #
        # TODO: Check logs

        # compile metadata
        self._result = utils.prepare_metadata(self._config, self._extra)
        self._result.update({'profiles': {}})

        # Get results from each benchmark
        for bench in self.selected_benchmarks:
            try:
                result_path = os.path.join(
                    self._config['rundir'], self.RESULT_FILES[bench])
                with open(result_path, "r") as result_file:
                    _log.info("Reading result file: {}".format(result_path))

                    self._result['profiles'].update(
                        json.loads(result_file.read()))

            except Exception as e:
                _log.warning('Skipping {} because of {}'.format(bench, e))

        # Save complete json report
        with open(os.path.join(self._config['rundir'], self._config['file']), 'w') as fo:
            fo.write(json.dumps(self._result))

    def results(self):
        return self._result
