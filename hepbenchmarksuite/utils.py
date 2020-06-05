###############################################################################
# Copyright 2019-2020 CERN. See the COPYRIGHT file at the top-level directory
# of this distribution. For licensing information, see the COPYING file at
# the top-level directory of this distribution.
###############################################################################

import json
import time
import sys
import os
import logging
import subprocess
import socket

from datetime import datetime

from hepbenchmarksuite.plugins.extractor import Extractor

_log = logging.getLogger(__name__)

def run_hepspec(conf, bench):
    """
    Run HEPSpec benchmark.

    Args:
      conf:  A dict containing configuration.
      bench: A string with the benchmark to run.

    """

    _log.debug("Configuration in use for benchmark {}: {}".format(bench, conf))

    # Config section to use
    hs06 = conf['hepspec06']

    # Select run mode: docker, singularity, podman, etc
    run_mode = conf['global']['mode']

    # HEPspec run arguments
    _run_args = "-b {0} -w {1} -p {2} -n {3} -u {4}".format(bench,
                                                           conf['global']['rundir'],
                                                           hs06['hepspec_volume'],
                                                           conf['global']['mp_num'],
                                                           hs06['url_tarball'])

    cmd = {
          'docker'      : "docker run --network=host -v {0}:{0} -v {1}:{1} {2} {3}".format(conf['global']['rundir'],
                                                                                           hs06['hepspec_volume'],
                                                                                           hs06['image'],
                                                                                           _run_args),
          'singularity' : "SINGULARITY_CACHEDIR={0}/singularity_cachedir singularity run -B {0}:{0} -B {1}:{1} docker://{2} {3}".format(conf['global']['rundir'],
                                                                                                                                        hs06['hepspec_volume'],
                                                                                                                                        hs06['image'],
                                                                                                                                        _run_args)
    }

    # Start benchmark
    _log.debug(cmd[run_mode])
    exec_wait_benchmark(cmd[run_mode])

def exec_wait_benchmark(cmd_str):
    """
    Accepts command string to execute and waits for process to finish

    Args:
      cmd_str: Command to execute.

    Returns:
      An integer with the error code
    """

    _log.debug("Excuting command: {}".format(cmd_str))

    cmd = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Output stdout from child process
    line = cmd.stdout.readline()
    while line:
       sys.stdout.write(line.decode('utf-8'))
       line = cmd.stdout.readline()

    # Wait until process is complete
    cmd.wait()

    # Check for errors
    if cmd.returncode != 0:
      _log.error("Benchmark execution failed; returncode = {}.".format(cmd.returncode))

    return cmd.returncode


def convert_tags_to_json(tag_str):
    """
    Convert tags string to json

    Args:
      tag_str: String to be converted to json.

    Returns:
      A dict containing the tags.
    """

    _log.info("User specified tags: {}".format(tag_str))

    # Check if user provided a valid tag string to be converted to json
    try:
      tags = json.loads(tag_str)

    except:
      # User provided wrong format. Default tags are provided.
      _log.warning("Not a valid tag json format specified: {}".format(tag_str))
      tags = {}

    return tags


def exec_cmd(cmd_str):
   """
   Executes a command string and returns its output

   Args:
     cmd_str: A string with the command to execute.

   Returns:
     A string with the output.
   """

   _log.debug("Excuting command: {}".format(cmd_str))

   cmd = subprocess.Popen(cmd_str, shell=True, executable='/bin/bash',  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   cmd_reply, cmd_error = cmd.communicate()

   # Check for errors
   if cmd.returncode != 0:
     cmd_reply = "not_available"
     _log.error(cmd_error)

   else:
     # Convert bytes to text and remove \n
     try:
       cmd_reply = cmd_reply.decode('utf-8').rstrip()
     except UnicodeDecodeError:
       _log.error("Failed to decode to utf-8.")

   return cmd_reply


def get_version():
    # TODO
    # Version of metadata to be used in ElasticSearch tagging
    return "2.0-dev"

def get_host_ips():
    """
    Get external facing system IP from default route, do not rely on hostname

    Returns:
      A string containing the ip
    """

    ip_address = exec_cmd("ip route get 1 | awk '{print $NF;exit}'")
    return ip_address

def prepare_metadata(params, extra):
    """
    Constructs a json with cli inputs and extra fields

    Args:
      cli_inputs: Arguments that were passed directly with cli
      extra:  Extra dict with fields to include

    Returns:
      A dict containing hardware metadata, tags, flags & extra fields
    """

    # Create output metadata
    result = {'host':{}}
    result.update({
        '_id'            : "{}_{}".format(params['uid'], extra['start_time']),
        '_timestamp'     : extra['start_time'],
        '_timestamp_end' : extra['end_time'],
        'json_version'   : get_version()
    })

    result['host'].update({
        'hostname': socket.gethostname(),
        'ip'      : get_host_ips(),
    })

    for i in ['UID', 'tags']:
      try:
        result['host'].update({"{}".format(i) : params[i]})
      except:
        result['host'].update({"{}".format(i): "not_defined"})

    # Hep-benchmark-suite flags
    FLAGS = {
        'mp_num' : params['mp_num'],
    }

    result['host'].update({
        'FLAGS'  : FLAGS,
    })

    # Collect Software and Hardware metadata from hwmetadata plugin
    hw=Extractor()

    result['host'].update({
        'SW': hw.collect_SW(),
        'HW': hw.collect_HW(),
    })

    return result


def print_results(results):
    """
    Prints the results in a human-readable format

    Args:
      results: A dict containing the results['profiles']

    """

    print("\n\n=========================================================")
    print("BENCHMARK RESULTS FOR {}".format(results['host']['hostname']))
    print("=========================================================")
    print("Suite start: {}".format(results['_timestamp']))
    print("Suite end:   {}".format(results['_timestamp_end']))
    print("Machine CPU Model: {}".format(results['host']['HW']['CPU']['CPU_Model']))

    p = results['profiles']
    bmk_print_action = {
        "db12":      lambda x: "DIRAC Benchmark = %.3f (%s)" % (float(p[x]['value']),p[x]['unit']),
        "hs06_32":   lambda x: "HS06 32 bit Benchmark = %s" %p[x]['score'],
        "hs06_64":   lambda x: "HS06 64 bit Benchmark = %s" %p[x]['score'],
        "spec2017":  lambda x: "SPEC2017 64 bit Benchmark = %s" %p[x]['score'],
        "hepscore":  lambda x: "HEPSCORE Benchmark = %s over benchmarks %s" % (round(p[x]['score'],2), p[x]['benchmarks'].keys())  ,
    }

    for bmk in sorted(results['profiles']):
        # this try covers two cases: that the expected printout fails or that the item is not know in the print_action
        try:
            print(bmk_print_action[bmk](bmk))
        except:
            print("{} : {}".format(bmk,results['profiles'][bmk]))


def print_results_from_file(json_file):
    """
    Prints the results from a json file

    Args:
      json_file: A json file with results

    """
    with open(json_file, 'r') as jfile:
       print_results(json.loads(jfile.read()))

