###############################################################################
# Copyright 2019-2020 CERN. See the COPYRIGHT file at the top-level directory
# of this distribution. For licensing information, see the COPYING file at
# the top-level directory of this distribution.
###############################################################################

import json
import time
import sys
import os
import xml.etree.ElementTree as ET
import argparse
import re
import multiprocessing
import logging

from datetime import datetime

from hepbenchmarksuite.plugins.extractor import Extractor


logger = logging.getLogger(__name__)

def extract_values(line):
    """Extract the values from the line and return a dictionary with the value, error, and unit"""

    values = line[line.find("(")+1:line.find(")")]
    value = values[:values.find("+")].strip()
    deviation = values[values.find("+/-")+3:].strip()
    unit = line[line.find(")")+1:].strip()
    if unit == 'ms':
            value = '%.5f' % (float(value)/1000)
            deviation = '%.5f' % (float(deviation)/1000)
            unit = 's'
    if float(deviation) == 0:
        return {'value': float(value), 'unit':unit}
    else:
        return {'value': float(value), 'error': float(deviation), 'unit':unit}


def parse_kv(rundir):
    # This code should be reviewed
    # NOTE: this will fail if KV did not run
    result = {'kv': {'start': int(os.environ['init_kv_test']),
                     'end': int(os.environ['end_kv_test']),
              }}

    file_name = rundir+"/KV/atlas-kv_summary.json"
    file = open(file_name, "r")
    result['kv'].update(json.loads(file.read()))
    return result

def parse_hepscore(rundir):
    result = {}
    file_name = rundir+"/HEPSCORE/hepscore_result.json"
    file = open(file_name, "r")
    result['hep-score'] = json.loads(file.read())
    return result

def insert_print_action(alist,akey,astring,adic):
    alist["lambda"].append(lambda x: astring%adic[x])
    alist["key"].append(akey)
    return alist


def print_results_kv(r):
    return 'KV cpu performance [evt/sec]: score %.2f over %d copies. Min Value %.2f Max Value %.2f'%(r['wl-scores']['sim'],r['copies'],r['wl-stats']['min'],r['wl-stats']['max'])

#-----------------------------------------

def parse_metadata(cli_inputs, extra):
    """
    Constructs a json with cli inputs and extra fields

    Args:
      cli_inputs: Arguments that were passed directly with cli
      extra:  Extra dict with fields to include

    Returns:
      A dict containing hardware metadata, tags, flags & extra fields
    """

    # Convert user tags to json format
    def convertTagsToJson(tag_str):
      logger.info("User specified tags: {}".format(cli_inputs.tags))

      # Check if user provided a valid tag string to be converted to json
      try:
        tags = json.loads(tag_str)

      except:
        # User provided wrong format. Default tags are provided.
        logger.warning("Not a valid tag json format specified: {}".format(tag_str))
        tags = {
                "pnode":    "not_defined",
                "freetext": "not_defined",
                "cloud":    "not_defined",
                "VO":       "not_defined"
         }
      return tags

    # Hep-benchmark-suite flags
    FLAGS = {
        'mp_num' : cli_inputs.mp_num,
    }

    # Get json metadata version from install folder
    install_dir, _ = os.path.split(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(install_dir,'VERSION')) as version_file:
        _json_version = version_file.readline()

    # Create output metadata
    result = {'host':{}}
    result.update({
        '_id'            : "{}_{}".format(cli_inputs.id, extra['start_time']),
        '_timestamp'     : extra['start_time'],
        '_timestamp_end' : extra['end_time'],
        'json_version'   : "2.0"
    })

    result['host'].update({
        'ip'             : cli_inputs.ip,
        'hostname'       : cli_inputs.name,
        'UID'            : cli_inputs.id,
        'FLAGS'          : FLAGS,
        'TAGS'           : convertTagsToJson(cli_inputs.tags),
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
    print("RESULTS OF THE OFFLINE BENCHMARK FOR CLOUD {}".format(results['host']['TAGS']['cloud']))
    print("=========================================================")
    print("Suite start {}".format(results['_timestamp']))
    print("Suite end   {}".format(results['_timestamp_end']))
    print("Machine CPU Model: {}".format(results['host']['HW']['CPU']['CPU_Model']))

    p = results['profiles']
    bmk_print_action = {
        "whetstone": lambda x: "Whetstone Benchmark = %s (MWIPS)" %p[x]['score'],
        "kv":        lambda x: print_results_kv(p[x]),
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

