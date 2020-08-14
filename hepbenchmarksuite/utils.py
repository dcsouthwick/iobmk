###############################################################################
# Copyright 2019-2020 CERN. See the COPYRIGHT file at the top-level directory
# of this distribution. For licensing information, see the COPYING file at
# the top-level directory of this distribution.
###############################################################################

import json
import logging
import os
import socket
import subprocess
import sys
import yaml

from hepbenchmarksuite.plugins.extractor import Extractor

_log = logging.getLogger(__name__)


def validate_spec(conf, bench):
    """
    Check if the configuration is valid for hepspec06.

    Args:
      conf:  A dict containing configuration.

    Returns:
      Error code: 0 OK , 1 Not OK
    """

    _log.debug("Configuration to apply validation: {}".format(conf))

    # Config section to use
    if bench in ['hs06_32', 'hs06_64']:
        spec = conf['hepspec06']

    elif bench in ['spec2017']:
        spec = conf['spec2017']

    # Required params to perform an HS06 benchmark
    SPEC_REQ = ['image', 'hepspec_volume']

    try:
        # Check what is missing from the config file in the hepspec06 category
        missing_params = list(filter(lambda x: spec.get(x) is None, SPEC_REQ))

        if len(missing_params) >= 1:
            _log.error("Required parameter not found in configuration: {}".format(missing_params))
            return 1

    except KeyError:
        _log.error("Not configuration found for HS06")
        return 1

    return 0


def run_hepscore(conf):
    """
    Import and run hepscore
    This method is temporary, as tag 1.0rc requires reading files from disk
    """
    try:
        from hepscore import HEPscore
    except ImportError:
        _log.error("Failed to import hepscore!")
        _log.warn("Skipping hepscore: unable to import")
        raise
    # hepscore constructor cannot handle excess keys...
    # hs = HEPscore(**self._config_full)

    # Override output directory so suite can find results
    # will write results to resultsdir/HEPscore19.json
    hepscore_overrides = {'cec': conf['global']['mode'],
                          'resultsdir': conf['global']['rundir']+'/HEPSCORE'}

    os.makedirs(hepscore_overrides['resultsdir'], exist_ok=True)
    hs = HEPscore(**hepscore_overrides)
    # Empty args defaults to hepscore distributed yaml
    # hs.read_and_parse_conf()
    # There is no way to pass config arguments to hepscore, it demands reading from disk
    hepscore_temp = {'hepscore_benchmark': conf['hepscore_benchmark']}
    hepscore_conf_path = os.path.join(conf['global']['rundir'], 'hepscore.yaml')
    with open(hepscore_conf_path, 'w') as conf_file:
        yaml.dump(hepscore_temp, conf_file)

    hs.read_and_parse_conf(hepscore_conf_path)
    os.remove(hepscore_conf_path)

    # hepscore flavor of error propagation
    # run() returns score from last workload if successful
    returncode = hs.run()
    if returncode >= 0:
        hs.gen_score()
        hs.write_output("json",
                        os.path.join(conf['global']['rundir'],
                                     'HEPSCORE/hepscore_result.json'))
    return returncode


def run_hepspec(conf, bench):
    """
    Run HEPSpec benchmark.

    Args:
      conf:  A dict containing configuration.
      bench: A string with the benchmark to run.

    Return:
      POSIX exit code from subprocess
    """

    _log.debug("Configuration in use for benchmark {}: {}".format(bench, conf))

    # Config section to use
    if bench in ['hs06_32', 'hs06_64']:
        spec = conf['hepspec06']

    elif bench in ['spec2017']:
        spec = conf['spec2017']

    # Select run mode: docker, singularity, podman, etc
    run_mode = conf['global']['mode']

    # Possible hepspec06 arguments
    spec_args = {
      'bench'          : ' -b {}'.format(bench),
      'iterations'     : ' -i {}'.format(spec.get('iterations')),
      'mp_num'         : ' -n {}'.format(conf['global'].get('mp_num')),
      'hepspec_volume' : ' -p {}'.format(spec.get('hepspec_volume')),
      'bmk_set'        : ' -s {}'.format(spec.get('bmk_set')),
      'url_tarball'    : ' -u {}'.format(spec.get('url_tarball')),
      'workdir'        : ' -w {}'.format(conf['global'].get('rundir')),
    }
    _log.debug("spec arguments: {}". format(spec_args))

    # Populate CLI from the global configuration section
    _run_args = spec_args['bench'] + spec_args['workdir'] + spec_args['mp_num']

    # Populate CLI from the hepspec06 configuration section
    # Removing image key from this population since its specified bellow at command level
    populate_keys = [*spec.keys()]
    populate_keys.remove('image')

    for k in populate_keys:
        try:
            _run_args += spec_args[k]

        except KeyError as e:
            _log.error("Not a valid HEPSPEC06 key: {}.".format(e))

    # Command specification
    cmd = {
        'docker': "docker run --network=host -v {0}:{0}:Z -v {1}:{1}:Z {2} {3}"
            .format(conf['global']['rundir'],
                    spec['hepspec_volume'],
                    spec['image'],
                    _run_args),
        'singularity': "SINGULARITY_CACHEDIR={0}/singularity_cachedir singularity run -B {0}:{0} -B {1}:{1} docker://{2} {3}"
            .format(conf['global']['rundir'],
                    spec['hepspec_volume'],
                    spec['image'],
                    _run_args)
    }

    # Start benchmark
    _log.debug(cmd[run_mode])
    returncode = exec_wait_benchmark(cmd[run_mode])
    return returncode


def exec_wait_benchmark(cmd_str):
    """
    Accepts command string to execute and waits for process to finish

    Args:
      cmd_str: Command to execute.

    Returns:
      An POSIX exit code (0 through 255)
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

    except Exception:
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

    cmd = subprocess.Popen(cmd_str, shell=True, executable='/bin/bash', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cmd_reply, cmd_error = cmd.communicate()

    # Check for errors
    if cmd.returncode != 0:
        cmd_reply = "not_available"
        _log.error(cmd_error.decode('utf-8').rstrip())

    else:
        # Convert bytes to text and remove \n
        try:
            cmd_reply = cmd_reply.decode('utf-8').rstrip()
        except UnicodeDecodeError:
            _log.error("Failed to decode to utf-8.")

    return cmd_reply, cmd.returncode


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

    ip_address, _ = exec_cmd("ip route get 1 | awk '{print $NF;exit}'")
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
    result = {'host': {}}
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
            result['host'].update({"{}".format(i): params[i]})
        except:
            result['host'].update({"{}".format(i): "not_defined"})

    # Hep-benchmark-suite flags
    FLAGS = {
        'mp_num': params['mp_num'],
    }

    result['host'].update({
        'FLAGS': FLAGS,
    })

    # Collect Software and Hardware metadata from hwmetadata plugin
    hw = Extractor()

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
    print("Machine CPU Model: {}".format(
        results['host']['HW']['CPU']['CPU_Model']))

    p = results['profiles']
    bmk_print_action = {
        "db12"    : lambda x: "DIRAC Benchmark = %.3f (%s)" % (float(p[x]['value']), p[x]['unit']),
        "hs06_32" : lambda x: "HS06 32 bit Benchmark = %s" % p[x]['score'],
        "hs06_64" : lambda x: "HS06 64 bit Benchmark = %s" % p[x]['score'],
        "spec2017": lambda x: "SPEC2017 64 bit Benchmark = %s" % p[x]['score'],
        "hepscore": lambda x: "HEPSCORE Benchmark = %s over benchmarks %s" % (round(p[x]['score'], 2), p[x]['benchmarks'].keys()),
    }

    for bmk in sorted(results['profiles']):
        # this try covers two cases: that the expected printout fails or that the item is not know in the print_action
        try:
            print(bmk_print_action[bmk](bmk))
        except:
            print("{} : {}".format(bmk, results['profiles'][bmk]))


def print_results_from_file(json_file):
    """
    Prints the results from a json file

    Args:
      json_file: A json file with results

    """
    with open(json_file, 'r') as jfile:
        print_results(json.loads(jfile.read()))
