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

from datetime import datetime

from hepbenchmarksuite.plugins.extractor import Extractor

_log = logging.getLogger(__name__)

def parse_hepscore(rundir):
    result = {}
    file_name = rundir+"/HEPSCORE/hepscore_result.json"
    file = open(file_name, "r")
    result['hep-score'] = json.loads(file.read())
    return result

#-----------

def exec_cmd(cmd_str):
    """ Accepts command string and returns output. """

    _log.debug("Excuting command: {}".format(cmd_str))

    cmd = subprocess.Popen(cmd_str, shell=True, executable='/bin/bash',  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cmd_reply, cmd_error = cmd.communicate()

    # Check for errors
    if cmd.returncode != 0:
      _log.error(cmd_error)
      cmd_reply = cmd_error

    else:
      # Convert bytes to text and remove \n
      try:
        cmd_reply = cmd_reply.decode('utf-8').rstrip()
      except UnicodeDecodeError:
        _log.error("Failed to decode to utf-8.")

    return cmd_reply



#-----------------------------------------
def convertTagsToJson(tag_str):
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
      tags = {
              "pnode":    "not_defined",
              "freetext": "not_defined",
              "cloud":    "not_defined",
              "VO":       "not_defined"
       }
    return tags


def get_version():
    # WIP
    # Get json metadata version from install folder
    install_dir, _ = os.path.split(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(install_dir,'VERSION')) as version_file:
        _json_version = version_file.readline()

    return "2.0-dev"

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

    for i in ['ip', 'hostname', 'UID', 'tags']:
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
    print("RESULTS OF THE OFFLINE BENCHMARK FOR CLOUD {}".format(results['host']['tags']['cloud']))
    print("=========================================================")
    print("Suite start {}".format(results['_timestamp']))
    print("Suite end   {}".format(results['_timestamp_end']))
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

