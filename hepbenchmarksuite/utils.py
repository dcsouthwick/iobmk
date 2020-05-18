###############################################################################
# Copyright 2019-2020 CERN. See the COPYRIGHT file at the top-level directory
# of this distribution. For licensing information, see the COPYING file at
# the top-level directory of this distribution.
###############################################################################

import json
import time
import sys
import os
from os import listdir
import xml.etree.ElementTree as ET
import argparse
import re
import multiprocessing
import logging
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


def fill_results(result, key, lines, i):
    entries = lines[i][lines[i].find("=")+1:lines[i].find(")")].strip()
    cpu = extract_values(lines[i+1])
    real = extract_values(lines[i+2])
    vmem = extract_values(lines[i+3])
    result.update({key: {'entries': int(entries),
                         'cpu': cpu,
                         'real': real,
                         'vmem': vmem
                        }
                   })


def fill_memory_results(result, key, lines, i):
    def extract_memory_value(line):
        value = line[line.find("INFO")+len("INFO"):]
        value = value[value.find(":")+2:].strip()
        unit = value[value.find(" ")+1:].strip()
        value = value[:value.find(" ")]
        return {'value': float(value), 'unit':unit}

    result.update({key:{ 'vm_data': extract_memory_value(lines[i+1]),
                    'vm_exe': extract_memory_value(lines[i+2]),
                    'VmHWM': extract_memory_value(lines[i+3]),
                    'VmLck': extract_memory_value(lines[i+4]),
                    'VmLib': extract_memory_value(lines[i+5]),
                    'VmPTE': extract_memory_value(lines[i+6]),
                    'VmPeak': extract_memory_value(lines[i+7]),
                    'VmRSS': extract_memory_value(lines[i+8]),
                    'VmSize': extract_memory_value(lines[i+9]),
                    'VmStk': extract_memory_value(lines[i+10]),
                    'VmSwap': extract_memory_value(lines[i+11])}})


def fill_memory_leak_results(result, key, lines, i):
    def extract_memory_value(line):
        value = line[line.find("INFO")+len("INFO"):]
        value = value[value.find(":")+2:].strip()
        unit = value[value.find(" ")+1:].strip()
        value = value[:value.find(" ")]
        if unit == 'ms':
            value = round(value/1000, 5)
            unit = 's'
        return {'value': float(value), 'unit':unit}
        return float(value)
    result.update({key: {'first-evt': extract_memory_value(lines[i+1]),
                         '10th -evt':extract_memory_value(lines[i+2]),
                         'last -evt':extract_memory_value(lines[i+3]),
                         'evt  2-20':extract_memory_value(lines[i+4]),
                         'evt 21-50':extract_memory_value(lines[i+5]),
                         'evt 51+':extract_memory_value(lines[i+6])} })

def parse_whetstone(rundir):
    file_name = rundir+"/whets/whets.res"

    try:
        output = open(file_name,'r').readlines()
    except IOError:
        #print "INFO: parsing - There are no results for whetstone, assuming it didn't run"
        raise
    except:
        raise

    # Avg all scores
    scores=[]
    for line in output:
        if "MWIPS" in line:
            scores.append(float(" ".join(line.split()).split(' ')[1]))

    global_score = "n/a"
    if scores:
        global_score=sum(scores)/float(len(scores))


    results = {"whetstone": {"units": "MWIPS", "score": global_score}}

    return results

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

def parse_metadata(args):
#    start_time = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(int(os.environ['init_tests'])))
#    end_time   = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(int(os.environ['end_tests'])))
    start_time = 2
    end_time   = 4
    # Convert user tags to json format
    def convertTagsToJson(tag_str):
        logger.info("User specified tags: %s " % args.tags)

        # Check if user provided a valid tag string to be converted to json
        try:
            tags = json.loads(tag_str)

        except:
            # User provided wrong format. Default tags are provided.
            logger.warning("Not a valid tag json format specified: %s" % tag_str)
            tags = {
                "pnode":    "not_defined",
                "freetext": "not_defined",
                "cloud":    "not_defined",
                "VO":       "not_defined"
            }
        return tags

    # Hep-benchmark-suite flags
    FLAGS = {
        'mp_num' : args.mp_num,
    }

    # Get json metadata version from install folder
    install_dir, _ = os.path.split(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(install_dir,'VERSION')) as version_file:
        _json_version = version_file.readline()

    # Create output metadata
    result = {'host':{}}
    result.update({
        '_id'            : "%s_%s" % (args.id, start_time),
        '_timestamp'     : start_time,
        '_timestamp_end' : end_time,
        'json_version'   : _json_version
    })

    result['host'].update({
        'ip'             : args.ip,
        'hostname'       : args.name,
        'UID'            : args.id,
        'FLAGS'          : FLAGS,
        'TAGS'           : convertTagsToJson(args.tags),
    })

    # Collect Software and Hardware metadata from hwmetadata plugin
    hw=Extractor()

    result['host'].update({
        'SW': hw.collect_SW(),
        'HW': hw.collect_HW(),
    })

    return result

def insert_print_action(alist,akey,astring,adic):
    alist["lambda"].append(lambda x: astring%adic[x])
    alist["key"].append(akey)
    return alist


def print_results_kv(r):
    return 'KV cpu performance [evt/sec]: score %.2f over %d copies. Min Value %.2f Max Value %.2f'%(r['wl-scores']['sim'],r['copies'],r['wl-stats']['min'],r['wl-stats']['max'])


def print_results(results):

    print ("\n\n=========================================================")
    print ("RESULTS OF THE OFFLINE BENCHMARK FOR CLOUD %s" % results['host']['TAGS']['cloud'])
    print ("=========================================================")
    print ("Suite start %s " % results['_timestamp'])
    print ("Suite end   %s" % results['_timestamp_end'])
    print ("Machine CPU Model: %s" %  results['host']['HW']['CPU']['CPU_Model'])

    p = results['profiles']
    bmk_print_action = {
        "whetstone": lambda x: "Whetstone Benchmark = %s (MWIPS)" %p[x]['score'],
        "kv": lambda x: print_results_kv(p[x]),
        "DB12": lambda x: "DIRAC Benchmark = %.3f (%s)" % (float(p[x]['value']),p[x]['unit']),
        "hs06_32": lambda x: "HS06 32 bit Benchmark = %s" %p[x]['score'],
        "hs06_64": lambda x: "HS06 64 bit Benchmark = %s" %p[x]['score'],
        "spec2017": lambda x: "SPEC2017 64 bit Benchmark = %s" %p[x]['score'],
        "hepscore": lambda x: "HEPSCORE Benchmark = %s over benchmarks %s" % (round(p[x]['score'],2), p[x]['benchmarks'].keys())  ,
        "hyperbenchmark": lambda x:print_hyperbenchmark(p[x])
    }

    for bmk in sorted(results['profiles']):
        #this try covers two cases: that the expected printout fails or that the item is not know in the print_action
        try:
            print (bmk_print_action[bmk](bmk))
        except:
            print ("%s : %s" %(bmk,results['profiles'][bmk]))

def print_results_from_file(afile):
    print_results(json.loads(open(afile, 'r').read()))

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--id",     nargs='?', help="UID")
    parser.add_argument("-n", "--name",   nargs='?', help="hostname")
    parser.add_argument("-p", "--ip",     nargs='?', help="ip address")
    parser.add_argument("-f", "--file",   nargs='?', help="File to store the results", default="result_profile.json")
    parser.add_argument("-d", "--rundir", nargs='?', help="Directory where bmks ran")
    parser.add_argument("-m", "--mp_num",  nargs='?', help="Number of cpus to run the benchmarks.")
    parser.add_argument("-t", "--tags",   nargs='?',  help="Custom user tags.")
    args = parser.parse_args()

    result = parse_metadata(args)
    result.update({'profiles': {}})
    try:
        result['profiles'].update(parse_phoronix())
    except Exception as e:
        logger.warning('Skipping phoronix because of %s'%e)
    try:
        result['profiles'].update(parse_kv(args.rundir))
    except Exception as e:
        logger.warning('Skipping KV because of %s'%e)
        pass

    try:
        result['profiles'].update(json.loads(open(args.rundir+"/SPEC2017/spec2017_result.json", "r").read()))
    except Exception as e:
        logger.warning('Skipping SPEC2017 because of %s'%e)
    try:
        result['profiles'].update(json.loads(open(args.rundir+"/HS06/hs06_32_result.json", "r").read()))
    except Exception as e:
        logger.warning('Skipping hs06_32 because of %s'%e)
    try:
        result['profiles'].update(json.loads(open(args.rundir+"/HS06/hs06_64_result.json", "r").read()))
    except Exception as e:
        logger.warning('skipping hs06_64 because of %s'%e)
    try:
        result['profiles'].update({'hepscore':json.loads(open(args.rundir+"/HEPSCORE/hepscore_result.json", "r").read())})
    except Exception as e:
        logger.warning('skipping hepscore because of %s'%e)
    try:
        result['profiles'].update(parse_whetstone(args.rundir))
    except Exception as e:
        logger.warning('skipping whetstone because of %s'%e)
    try:
        if os.environ['HYPER_BENCHMARK'] != '':
            result['profiles'].update(parse_hyper_benchmark())
    except Exception as e:
        logger.warning('skipping HYPER_BENCHMARK because of %s'%e)
    try:
        if os.environ['DB12'] != '':
            result['profiles'].update({'DB12': {'value': float(os.environ['DB12']), 'unit': 'est. HS06'}})
    except Exception as ex:
        pass


    open(args.file, 'w').write(json.dumps(result))

    print_results_from_file(args.file)

    print("\nResults are stored in file %s" % args.file)
