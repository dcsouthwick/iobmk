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
import tarfile
import yaml

from importlib_metadata import version, PackageNotFoundError
from pkg_resources import parse_version

try:
    from importlib.resources import files
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    from importlib_resources import files


from hepbenchmarksuite.plugins.extractor import Extractor
from hepbenchmarksuite.exceptions import InstallHEPscoreFailure

_log = logging.getLogger(__name__)


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
        for root, dirs, files_ in os.walk(result_dir):
            for name in files_:
                if name.endswith('.json') or name.endswith('.log'):
                    archive.add(os.path.join(root, name))

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

def install_hepscore(package, force=False):
    """Install hepscore.

    Args:
      package: Package to be installed.
      force: To force installation.

    Raises:
      InstallHepScoreFailure: If it fails to install
    """

    runflags=["-m", "pip", "install", "--user"]

    if force:
        runflags.append("--force-reinstall")

    _log.info('Attempting the installation of hep-score.')
    _log.debug('Installation flags: '.format(runflags))

    try:
        subprocess.check_call([sys.executable, *runflags, package])

    except subprocess.CalledProcessError:
        _log.exception('Failed to install hep-score')
        raise InstallHEPscoreFailure

    _log.info('Installation of hep-score succeeded.')

def prep_hepscore(conf):
    """Prepare hepscore installation.

    Args:
      conf: A dict containing configuration.

    Returns:
      Error code: 0 OK , 1 Not OK
    """

    REQ_VERSION   = conf['hepscore']['version']
    HEPSCORE_REPO = 'git+https://gitlab.cern.ch/hep-benchmarks/hep-score.git'

    _log.info("Checking if hep-score is installed.")

    try:

        SYS_VERSION = version('hep-score')
        _log.info("Found existing installation of hep-score in the system: v{}".format(SYS_VERSION))

        # If the installation matches the one in the config file we can resume.
        if parse_version(REQ_VERSION) == parse_version(SYS_VERSION):
            _log.info("Installation matches requested version in the config file: {}".format(REQ_VERSION))
            return 0

        # Force the re-installation of desired version in the config
        else:
            _log.warning("Installed version ({}) differs from config file ({}) - forcing reinstall".format(SYS_VERSION,
                                                                                                           REQ_VERSION))

            try:
                install_hepscore(HEPSCORE_REPO+"@{}".format(REQ_VERSION), force=True)
            except InstallHEPscoreFailure:
                return 1

    except PackageNotFoundError:
        _log.info('Installation of hep-score not found in the system.')

        try:
            install_hepscore(HEPSCORE_REPO+"@{}".format(REQ_VERSION))
        except InstallHEPscoreFailure:
            return 1

    # Recursive call for the cases that we perform reinstall
    # but we want to repeat the same check sequence
    return prep_hepscore(conf)

def run_hepscore(suite_conf):
    """Import and run hepscore."""

    try:
        _log.info("Attempting to import hepscore")
        import hepscore
    except ImportError:
        _log.exception("Failed to import hepscore!")
        return -1

    # Abort if section is commented
    if 'hepscore' not in suite_conf:
        _log.error("The hepscore section was not found in configuration file.")
        sys.exit(1)

    # Use hepscore-distributed config by default
    if suite_conf['hepscore']['config'] == 'default':
        _log.info("Using default config provided by hepscore.")
        try:
            cfg_string    = files(hepscore).joinpath('etc/hepscore-default.yaml').read_text()
            hepscore_conf = yaml.safe_load(cfg_string)

        except Exception:
            _log.exception("Unable to load default config yaml.")
            return -1
    else:
        _log.error("Skipping hepscore default config. Loading user provided config: {}".format(suite_conf['hepscore']['config']))
        try:
            with open(suite_conf['hepscore']['config'], 'r') as alt_conf_file:
                hepscore_conf = yaml.safe_load(alt_conf_file)

        except FileNotFoundError:
            _log.error("Alternative hepscore config file not found: {}".format(suite_conf['hepscore']['config']))
            return -1

    # ensure same runmode as suite
    hepscore_conf['hepscore_benchmark']['settings']['container_exec'] = suite_conf['global']['mode']

    # Specify directory to output results
    hepscore_results_dir = os.path.join(suite_conf['global']['rundir'], 'HEPSCORE')

    # Initiate hepscore
    hs = hepscore.HEPscore(hepscore_conf, hepscore_results_dir)

    # hepscore flavor of error propagation
    # run() returns score from last workload if successful
    _log.info("Starting hepscore")
    _log.debug("Config in use: {}".format(hepscore_conf))

    returncode = hs.run()

    if returncode >= 0:
        hs.gen_score()

    hs.write_output("json", os.path.join(suite_conf['global']['rundir'], 'HEPSCORE/hepscore_result.json'))

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
        'bench'         : ' -b {}'.format(bench),
        'iterations'    : ' -i {}'.format(spec.get('iterations')),
        'mp_num'        : ' -n {}'.format(conf['global'].get('mp_num')),
        'hepspec_volume': ' -p {}'.format(spec.get('hepspec_volume')),
        'bmk_set'       : ' -s {}'.format(spec.get('bmk_set')),
        'url_tarball'   : ' -u {}'.format(spec.get('url_tarball')),
        'workdir'       : ' -w {}'.format(conf['global'].get('rundir'))
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

        except KeyError as err:
            _log.error("Not a valid HEPSPEC06 key: {}.".format(err))

    # Command specification
    cmd = {
        'docker': "docker run --network=host -v {0}:{0}:Z -v {1}:{1}:Z {2} {3}"
            .format(conf['global']['rundir'],
                    spec['hepspec_volume'],
                    spec['image'],
                    _run_args),
        'singularity': "SINGULARITY_CACHEDIR={0}/singularity_cachedir singularity run -B {1}:{1} -B {2}:{2} docker://{3} {4}"
            .format(conf['global']['parent_dir'],
                    conf['global']['rundir'],
                    spec['hepspec_volume'],
                    spec['image'],
                    _run_args)
    }

    # Start benchmark
    _log.debug(cmd[run_mode])
    returncode = exec_wait_benchmark(cmd[run_mode])
    return returncode


def exec_wait_benchmark(cmd_str):
    """Accept command string to execute and waits for process to finish.

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


def exec_cmd(cmd_str, env=None, output=False):
    """Execute a command string and returns its output.

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
        '_id'           : "{}_{}".format(params['uid'], extra['start_time']),
        '_timestamp'    : extra['start_time'],
        '_timestamp_end': extra['end_time'],
        'json_version'  : get_version()
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
        'SW': hw.collect_sw(),
        'HW': hw.collect_hw(),
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

    data = results['profiles']

    def parse_hepscore(data):
        # Attempt to use the new format of hepscore reporting
        # can be dropped in the future once metadata is standard
        try:
            result = round(data['report']['score'], 2)
        except KeyError:
            result = round(data['score'], 2)
        return "HEPSCORE Benchmark = {} over benchmarks {}".format(result, data['benchmarks'].keys())

    bmk_print_action = {
        "DB12"    : lambda x: "DIRAC Benchmark = %.3f (%s)" % (float(data[x]['value']), data[x]['unit']),
        "hs06_32" : lambda x: "HS06 32 bit Benchmark = {}".format(data[x]['score']),
        "hs06_64" : lambda x: "HS06 64 bit Benchmark = {}".format(data[x]['score']),
        "spec2017": lambda x: "SPEC2017 64 bit Benchmark = {}".format(data[x]['score']),
        "hepscore": lambda x: parse_hepscore(data[x]),
    }

    for bmk in sorted(results['profiles']):
        # This try covers two cases: that the expected printout fails
        # or that the item is not know in the print_action
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
