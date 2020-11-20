###############################################################################
# Copyright 2019-2020 CERN. See the COPYRIGHT file at the top-level directory
# of this distribution. For licensing information, see the COPYING file at
# the top-level directory of this distribution.
###############################################################################

import logging
import os
import subprocess
import sys
import yaml

from importlib_metadata import version, PackageNotFoundError
from pkg_resources import parse_version

try:
    from importlib.resources import files
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    from importlib_resources import files

from hepbenchmarksuite import utils
from hepbenchmarksuite.exceptions import InstallHEPscoreFailure

_log = logging.getLogger(__name__)


def validate_spec(conf, bench):
    """Check if the configuration is valid for hepspec06.

    Args:
      conf:  A dict containing configuration.

    Returns:
      Error code: 0 OK , 1 Not OK
    """
    _log.debug("Configuration to apply validation: %s", conf)

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
            _log.error("Required parameter not found in configuration: %s", missing_params)
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

    if len(os.environ['VIRTUAL_ENV'])>0:
        _log.info("Virtual environment detected: %s", os.environ['VIRTUAL_ENV'])
        _log.info("Installing hep-score in virtual environment.")
        runflags=["-m", "pip", "install"]

    if force:
        runflags.append("--force-reinstall")

    _log.info('Attempting the installation of hep-score.')
    _log.debug('Installation flags: %s', runflags)

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
        _log.info("Found existing installation of hep-score in the system: v%s", SYS_VERSION)

        # If the installation matches the one in the config file we can resume.
        if parse_version(REQ_VERSION) == parse_version(SYS_VERSION):
            _log.info("Installation matches requested version in the config file: %s", REQ_VERSION)
            return 0

        # Force the re-installation of desired version in the config
        else:
            _log.warning("Installed version (%s) differs from config file (%s) - forcing reinstall", SYS_VERSION,
                                                                                                     REQ_VERSION)

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

    # Use config provided from remote link
    elif "http" in suite_conf['hepscore']['config']:
        _log.info("Skipping hepscore default config. Loading config from remote: %s", suite_conf['hepscore']['config'])

        # Save the remote file to the user specified rundir
        hepscore_file_dest = os.path.join(suite_conf['global']['rundir'], "hepscore.yaml")

        # Download remote file
        error_code = utils.download_file(suite_conf['hepscore']['config'], hepscore_file_dest)

        # Succeeds on download, open file
        if error_code == 0:
            with open(hepscore_file_dest, 'r') as http_conf:
                hepscore_conf = yaml.safe_load(http_conf)
                _log.info("Using hepscore config: %s", hepscore_file_dest)
        else:
            return -1

    else:
        _log.error("Skipping hepscore default config. Loading user provided config: %s", suite_conf['hepscore']['config'])

        try:
            with open(suite_conf['hepscore']['config'], 'r') as alt_conf_file:
                hepscore_conf = yaml.safe_load(alt_conf_file)

        except FileNotFoundError:
            _log.error("Alternative hepscore config file not found: %s", suite_conf['hepscore']['config'])
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
    _log.debug("Config in use: %s", hepscore_conf)

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
    _log.debug("Configuration in use for benchmark %s: %s", bench, conf)

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
    _log.debug("spec arguments: %s", spec_args)

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
            _log.error("Not a valid HEPSPEC06 key: %s.", err)

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
    returncode = utils.exec_wait_benchmark(cmd[run_mode])
    return returncode
