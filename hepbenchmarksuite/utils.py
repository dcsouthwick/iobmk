###############################################################################
# Copyright 2019-2020 CERN. See the COPYRIGHT file at the top-level directory
# of this distribution. For licensing information, see the COPYING file at
# the top-level directory of this distribution.
###############################################################################

import json
import logging
try:
    from importlib.resources import files
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    from importlib_resources import files

import os
import shlex
import socket
import subprocess
import sys
import tarfile
import yaml

from hepbenchmarksuite.plugins.extractor import Extractor

_log = logging.getLogger(__name__)
bmk_env = os.environ.copy()


def export(result_dir, outfile):
    """Export all json and log files from a given dir.

    Args:
      result_dir: String with the directory to compress the files.
      outfile:    String with the filename to save.

    Returns:
      Error code: 0 OK , 1 Not OK
    """
    _log.info("Exporting *.json, *.log from {}...".format(result_dir))

    with tarfile.open(outfile, 'w:gz') as archive:
        # Respect the tree hierarchy on compressing
        for root, dirs, files in os.walk(result_dir):
            for name in files:
                if name.endswith('.json') or name.endswith('.log'):
                    archive.add(os.path.join(root,name))

    _log.info("Files compressed! The resulting file was created: {}".format(outfile))

    return 0


def validate_spec(conf, bench):
    """Check if the configuration is valid for hepspec06.

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
    """Import and run hepscore."""
    try:
        import hepscore
    except ImportError:
        _log.exception("Failed to import hepscore!")
        return -1

    # Use hepscore-distributed config if not provided:
    if 'hepscore_benchmark' not in conf:
        try:
            cfgString = files(hepscore).joinpath('etc/hepscore-default.yaml').read_text()
            conf.update(yaml.safe_load(cfgString))
        except Exception:
            _log.exception("Unable to load default config yaml")
            return -1

    # ensure same runmode as suite
    conf['hepscore_benchmark']['settings']['container_exec'] = conf['global']['mode']
    hepscore_resultsDir = os.path.join(conf['global']['rundir'], 'HEPSCORE')

    hs = hepscore.HEPscore(conf, hepscore_resultsDir)

    # hepscore flavor of error propagation
    # run() returns score from last workload if successful
    returncode = hs.run()
    if returncode >= 0:
        hs.gen_score()
    hs.write_output("json", os.path.join(conf['global']['rundir'], 'HEPSCORE/hepscore_result.json'))
    return returncode


def run_hepspec(conf, bench):
    """Run HEPSpec benchmark.

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
        'singularity': "singularity run -B {1}:{1} -B {2}:{2} docker://{3} {4}"
            .format(conf['global']['parent_dir'],
                    conf['global']['rundir'],
                    spec['hepspec_volume'],
                    spec['image'],
                    _run_args)
    }

    bmk_env["SINGULARITY_CACHEDIR"] = "{}/singuality_cachedir".format(conf['global']['parent_dir'])

    # Start benchmark
    _log.debug(cmd[run_mode])
    _, returncode = exec_cmd(cmd[run_mode], env)
    if returncode != 0:
        _log.error("Benchmark execution failed; returncode = {}.".format(returncode))
    return returncode


def convert_tags_to_json(tag_str):
    """Convert tags string to json.

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


def exec_cmd(cmd_str, env=None):
    """Execute a command string and returns its output.

    Args:
      cmd_str: A string with the command to execute.

    Returns:
      A string with the output.
    """
    _log.debug("Excuting command: {}".format(cmd_str))

    if "|" in cmd_str:
        cmds = cmd_str.split('|')
    else:
        cmds = [cmd_str]

    p = dict()
    for i, cmd in enumerate(cmds):
        if i == 0:
            p[i] = Popen(shlex.split(cmd), stdin=None,
                         stdout=PIPE, stderr=PIPE, encoding='utf-8')
        else:
            p[i] = Popen(shlex.split(cmd), stdin=p[i - 1].stdout,
                         stdout=PIPE, stderr=PIPE, encoding='utf-8')
    stdout, stderr = p[len(cmds) - 1].communicate()
    returncode = p[len(cmds) - 1].wait()
    # Check for errors
    if returncode != 0:
        stdout = "not_available"
        _log.error(stderr)

    return stdout, returncode


def get_version():
    """Version of metadata to be used in ElasticSearch tagging."""
    return "v2.1-dev"


def get_host_ips():
    """Get external facing system IP from default route, do not rely on hostname.

    Returns:
      A string containing the ip
    """
    ip_address, _ = exec_cmd("ip route get 1 | awk '{print $NF;exit}'")
    return ip_address


def prepare_metadata(params, extra):
    """Construct a json with cli inputs and extra fields.

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
    """Print the results in a human-readable format.

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
        "DB12"    : lambda x: "DIRAC Benchmark = %.3f (%s)" % (float(p[x]['value']), p[x]['unit']),
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
    """Print the results from a json file.

    Args:
      json_file: A json file with results
    """
    with open(json_file, 'r') as jfile:
        print_results(json.loads(jfile.read()))
