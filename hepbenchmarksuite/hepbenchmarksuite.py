###############################################################################
# Copyright 2019-2020 CERN. See the COPYRIGHT file at the top-level directory
# of this distribution. For licensing information, see the COPYING file at
# the top-level directory of this distribution.
###############################################################################

import os
import json
import logging
from hepbenchmarksuite import DB12
from hepbenchmarksuite.utils import parse_metadata

_log = logging.getLogger(__name__)

class HepBenchmarkSuite(object):
  """********************************************************
                *** HEP-BENCHMARK-SUITE ***
   *********************************************************"""


  RESULT_FILES = {
      'hs06_32'  : '/HS06/hs06_32_result.json',
      'hs06_64'  : '/HS06/hs06_64_result.json',
      'spec2017' : '/SPEC2017/spec2017_result.json',
      'hepscore' : '/HEPSCORE/hepscore_result.json',
      'db12'     : 'db12_result.json',
  }


  def __init__(self, items=None, args=None):
    """Initialize setup"""
    self._bench_queue        = items
    self.selected_benchmarks = items.copy()
    self.args                = args

  def start(self):
    _log.info ("Starting benchmark suite")
    if self.preflight() == 0:
      self.run()

  def preflight(self):
    _log.info ("Running pre-flight checks")
    return 0

  def run(self):
    if len(self._bench_queue) == 0:
      self.cleanup()
    else:

      bench2run = self.dequeue()
      print ("Running benchmark: ", bench2run)
      print ("Benchmarks left:", self._bench_queue)

      if bench2run == 'db12':
        DB12.run_DB12(rundir=".", cpu_num=2)

      self.check_lock()

  def dequeue(self):
      return self._bench_queue.pop(0)

  def check_lock(self):
    # loop until lock is released from benchmark
    # print(os.path.exists("bench.lock"))
    # resume
    self.run()

  def cleanup(self):
    # Check logs
    # compile metadata
    result = parse_metadata(self.args)
    result.update({'profiles': {}})

    # Get results from benchmarks
    for bench in self.selected_benchmarks:
      try:
          with open(self.RESULT_FILES[bench], "r") as result_file:
            result['profiles'].update(json.loads(result_file.read()))

      except Exception as e:
        _log.warning('Skipping {} because of {}'.format(bench,e))

    with open("output.json", 'w') as fo:
      fo.write(json.dumps(result))

    print (result)
