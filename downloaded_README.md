# HEPscore

## Table of Contents

1. [About](#about)  
2. [HEPscore20POC Benchmark](#hepscore20poc-benchmark)
3. [Downloading and Installing HEPscore](#downloading-and-installing-hepscore)  
4. [Dependencies](#dependencies)  
5. [Configuring HEPscore](#configuring-hepscore)  
    1. [Parameters](#parameters)  
6. [Feedback and Support](#feedback-and-support)

## About

The HEPscore application orchestrates the execution of user-configurable
benchmark suites based on individual benchmark containers.  It runs the
specified benchmark containers in sequence, collects their results, and
computes a final overall score.  HEPscore is specifically designed for
use with containers from the [HEP Workloads project](
https://gitlab.cern.ch/hep-benchmarks/hep-workloads).
However, any benchmark containers stored in a Docker/Singularity
registry, or filesystem directory, which conform to the HEP Workloads'
output JSON schema, are potentially usable.  Both Singularity and Docker 
are supported for container execution.  By default, if no configuration 
is passed to HEPscore, the "HEPscore20POC" benchmark is run.

## HEPscore20POC Benchmark

HEPscore20POC is a benchmark based on containerized HEP workloads that
the HEPiX Benchmarking Working Group is targeting to eventually replace
HEPSPEC06 as the standard HEPiX/WLCG benchmark.  It is currently in a
proof of concept development state, and consists of the following workloads 
from the
[HEP Workloads project](
https://gitlab.cern.ch/hep-benchmarks/hep-workloads):  
atlas-gen-bmk  
belle2-gen-sim-reco-bmk  
cms-gen-sim-bmk  
cms-digi-bmk  
cms-reco-bmk  
lhcb-gen-sim-bmk  
You can view the YAML HEPscore configuration for HEPscore20POC by
executing ```hep-score -p```.

The benchmark will take 5+ hours to execute on modern hardware.

**NOTE**: ~20 GB of free disk space in your Singularity or Docker
cache area, and 320 MB/core of free space (e.g. 20 GB on 64 core host)
in the specified OUTDIR output directory is necessary to run the
HEPscore20POC benchmark.  If passed the ```-c``` (clean images) and 
```-C``` (clean files) command line options, hep-score will clean
the benchmark container images and output after execution, which will 
greatly reduce the amount of space needed to run.

It is also possible to run the benchmark containers out of the
"unpacked.cern.ch" CVMFS repo instead of the CERN gitlab Docker registry,
by passing ```hep-score``` the
[hepscore-cvmfs.yaml](https://gitlab.cern.ch/hep-benchmarks/hep-score/-/raw/master/hepscore/etc/hepscore20poc_0.8-cvmfs.yaml)
file shipped in the application's etc/ directory.  When running the
benchmark using the unpacked images in CVMFS, the Singularity cache area
is not utilized.

## Downloading  and Installing HEPscore

HEPscore must be installed using pip (<https://pypi.org/project/pip/>).  

To install as a regular user (suggested):  
```$ pip install --user git+https://gitlab.cern.ch/hep-benchmarks/hep-score.git```  
The ```hep-score``` script will then be accessible under ```~/.local/bin```.  

If you have administrator rights on your system and would like to install
hep-score and all dependencies in system Python/bin paths:  
```# pip install git+https://gitlab.cern.ch/hep-benchmarks/hep-score.git```

Alternatively, you can clone the hep-score git repository, and run the pip
installation out of the root directory of the repo:

```sh
$ git clone https://gitlab.cern.ch/hep-benchmarks/hep-score.git
$ cd hep-score
$ pip install --user .
```

**NOTE**: on RHEL/CentOS/Scientific Linux 7 hosts, where python 3 is not
the default python installation, it may be necessary to use ```pip3``` to
install instead of ```pip```.

Release tarfiles containing the Python wheel for the hepscore package, as
well as all dependency wheels, are available/published in the
[HEPscore release documentation](https://gitlab.cern.ch/hep-benchmarks/hep-score/-/releases).
An archive of all released wheel tarfiles is also available here: 
<https://hep-benchmarks.web.cern.ch/hep-score/releases/>.
These wheels can be used to install HEPscore via pip on hosts without
network connectivity.  To install, after downloading and untarring a
release tarfile, execute ```pip install --user hepscore_wheels/*.whl```.


## Dependencies

HEPscore requires a **Python 3.6+** installation.  The pip installation will pull
in all python module dependencies.  HEPscore should be used with **Singularity
3.5.3 and newer**, or **Docker 1.13 and newer**.  There are some known issues
when using HEPscore with earlier Singularity and Docker releases.

## Running HEPscore

```sh
usage: hep-score [-h] [-m [{singularity,docker}]] [-S] [-c] [-C]
                 [-f [CONFFILE]] [-r] [-o [OUTFILE]] [-y] [-p] [-V] [-v]
                 [OUTDIR]

positional arguments:
  OUTDIR                Base output directory.

optional arguments:
  -h, --help            show this help message and exit
  -m [{singularity,docker}], --container_exec [{singularity,docker}]
                        specify container platform for benchmark execution
                        (singularity [default], or docker).
  -S, --userns          enable user namespace for Singularity, if supported.
  -c, --clean           clean residual container images from system after run.
  -C, --clean_files     clean residual files & directories after execution.
                        Tar results.
  -f [CONFFILE], --conffile [CONFFILE]
                        custom config yaml to use instead of default.
  -r, --replay          replay output using existing results directory OUTDIR.
  -o [OUTFILE], --outfile [OUTFILE]
                        specify summary output file path/name.
  -y, --yaml            create YAML summary output instead of JSON.
  -p, --print           print configuration and exit.
  -V, --version         show program version number and exit
  -v, --verbose         enables verbose mode. Display debug messages.


Examples:
Run benchmarks via Docker, and display verbose information:
$ hep-score -v -m docker ./testdir

Run using Singularity (default) with a custom benchmark configuration:
$ hep-score -f /tmp/my-custom-bmk.yml /tmp
```

Singularity will be used as the container engine for the run, unless Docker
is specified on the hep-score commmandline (```-m docker```), or in the
benchmark configuration.

hep-score creates a HEPscore_DATE_TIME named directory under OUTDIR which
is used as the working directory for the sub-benchmark containers.  A detailed
log of the run of the application is also written to this directory:
BENCHMARK_NAME.log, where BENCHMARK_NAME is taken from the "name" parameter in
the YAML configuration ("HEPscore20POC.log" by default).

The final computed score will be printed to stdout ("Final score: XYZ"), and
also stored in a summary output JSON (or YAML, if ```-y``` is specified) file
under OUTDIR (unless an alternative location is specified with ```-o```).  This
file also contains all of the summary JSON output data from each sub-benchmark.

## Configuring HEPscore

An example hepscore YAML configuration is below:

```yaml
hepscore_benchmark:
  benchmarks:
    cms-reco-bmk:
      results_file: cms-reco_summary.json
      ref_scores:
        reco: 2.196
      weight: 1.0
      version: v2.1
      args:
        threads: 4
        events: 50
    lhcb-gen-sim-bmk:
      results_file: lhcb-gen-sim_summary.json
      ref_scores:
        gen-sim: 90.29
      weight: 1.0
      version: v2.1
      args:
        threads: 1
        events: 5
  settings:
    name: TestBenchmark
    reference_machine: "CPU Intel(R) Xeon(R) CPU E5-2630 v3 @ 2.40GHz"
    registry: docker://gitlab-registry.cern.ch/hep-benchmarks/hep-workloads
    method: geometric_mean
    repetitions: 3
    scaling: 355
    container_exec: singularity
```

All configuration parameters must be under the "hepscore_benchmark" key.

### Parameters

#### benchmarks (required)

DICTIONARY  
Specifies a list of benchmark containers to run, with associated settings:
see below

##### BENCHMARK_NAME (required)

DICTIONARY; where BENCHMARK_NAME is variable  
BENCHMARK_NAME denotes the name of the benchmark container to run.  See
per-benchmark settings below

###### ref_scores (required)

DICTIONARY  
List of sub-scores to collect from the benchmark container output
JSON, with reference scores from the specified "reference_machine".  Each
sub-score is divided by its reference score, and the geometric mean is
taken from the results to compute a final score for the benchmark
container

###### version (required)

STRING  
The version of the benchmark container to execute

###### results_file

STRING ; defaults to BENCHMARK_NAME.json, where BENCHMARK_NAME
is the name of the benchmark container.  
The name of the benchmark container results JSON file.

###### args

DICTIONARY; default set by container  
Set options to pass to the benchmark container.  Typically, ```events``` to
set the number of events, ```threads``` for the number threads, ```copies``` 
for the number of copies, and ```debug```to enable debugging output

###### gpu

BOOL; default = false  
Enable GPU support in Singularity/Docker call.

###### weight

FLOAT; default = 1.0  
Sets the weight for the benchmark container when calculating the overall
score

###### registry

STRING; defaults to the primary registry specified in "settings"  
Allows for overriding the registry to use for this container.  See
"registry", under "settings" below, for more information

#### settings (required)

DICTIONARY  
Defines overall benchmark application settings/information below  

##### name (required)

STRING  
The name of the overall benchmark/configuration

##### reference_machine (required)

STRING  
Specifies host/configuration where the benchmark container scores have
been normalized to 1.0.  All reported scores are then relative to the
performance of this host

##### registry (required)

STRING  
The registry to run containers from.  Multiple URIs are permitted:
```docker://``` to specify a Docker registry, ```dir://``` (Singularity
only) to specify a local directory containing unpacked images or image
files, or ```shub://``` (Singularity only) to specify a Singularity
registry

##### method (required)

STRING  
The method for combining the sub-benchmark scores into a single score.
Currently only "geometric_mean" is supported.  This is actually a
weighted geometric mean, with weights taken from 'weight' configuration
parameter for each benchmark.

##### repetitions (required)

INTEGER  
The number of times each benchmark container should be run.  If the
number of runs is greater than one, the median of that container's
resulting scores is used

###### scaling  

FLOAT; default = 1.0  
The multi-benchmark score calculated via the "method" parameter is
multiplied by this value to compute the final score

##### container_exec

STRING; defaullt = "singularity"  
Allows one to specify the default container execution platform:
"singularity" and "docker" are supported.  This can be overridden on the
commandline

##### retries

INTEGER; default = 0  
Specifies how many times to retry running a container if it fails.

##### continue_fail

BOOL; default = false  
Defines whether hep-score should continue attempting to run other
sub-benchmarks, if a sub-benchmark fails and does not produce a
resulting score.  If true, and this condition occurs, an overall/final
score will *not* be reported by the application, but runs of other
sub-benchmarks will continue.  This parameter is primarily useful for
testing and debugging purposes

## Feedback and Support
Feedback, and support questions are welcome in the HEP Benchmarks Project
[Discourse Forum](https://wlcg-discourse.web.cern.ch/c/hep-benchmarks).
You can also submit issues via 
[Gitlab](https://gitlab.cern.ch/hep-benchmarks/user-support/-/issues).

|     |     |     |
| --- | --- | --- |
| **qa-v1.0**     |  [![pipeline status](https://gitlab.cern.ch/hep-benchmarks/hep-score/badges/qa-v1.0/pipeline.svg)](https://gitlab.cern.ch/hep-benchmarks/hep-score/commits/qa-v1.0)     | ![code quality](https://gitlab.cern.ch/hep-benchmarks/hep-score/-/jobs/artifacts/qa-v1.0/raw/public/badges/pep8.svg?job=pep8) |
| **master**      |  [![pipeline status](https://gitlab.cern.ch/hep-benchmarks/hep-score/badges/master/pipeline.svg)](https://gitlab.cern.ch/hep-benchmarks/hep-score/commits/master)       | ![code quality](https://gitlab.cern.ch/hep-benchmarks/hep-score/-/jobs/artifacts/master/raw/public/badges/pep8.svg?job=pep8) |
