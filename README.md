# HEP Benchmark Suite

|   qa-v2.0 | master |
| --------- | -------- |
|   [![pipeline status](https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/badges/qa/pipeline.svg)](https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/-/pipelines?ref=qa-v2.0)     |  [![pipeline status](https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/badges/master/pipeline.svg)](https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/-/pipelines?ref=master)     |
[![coverage report](https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/badges/qa-v2.0/coverage.svg)](https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/-/commits/qa-v2.0)|[![coverage report](https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/badges/master/coverage.svg)](https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/-/commits/master)|

[[_TOC_]]


## About
The HEP Benchmark Suite is a toolkit which aggregates several different benchmarks
in one single application for characterizing the perfomance of individual and clustered heterogeneous hardware.

It is built in a modular approach to target the following use cases in HEP computing:

1. Mimic the usage of WLCG resources for experiment workloads
   * Run workloads representative of the production applications running on WLCG
1. Allow collection of a configurable number of benchmarks
   * Enable performance studies on heterogeneous hardware
1. Collect the hardware metadata and the running conditions
   * Compare the benchmark outcome under similar conditions
1. Have prompt feedback about executed benchmarks
   * By publishing results to a monitoring system
1. Probe randomly assigned slots in a cloud environment
   * In production can suggest deletion and re-provisioning of underperforming resources

## Benchmark suite architecture

*The figure shows the high level architecture of the benchmark suite.*


<div align="center">
![Benchmark Suite architectural view](doc/images/HEP-Benchmark-Suite.png)
</div>

A configurable sequence of benchmarks may be launched by the HEP Benchmark Suite.

Benchmark results are aggregated into a single JSON document, together with the hardware metadata (CPU model, host name, Data Centre name, kernel version, etc.)

Optionally, the final report can be sent to a transport layer, to be further digested and analysed by broker consumers.

Users may also execute the suite in stand-alone mode without result reporting. (see [How to run](#how-to-run) for further details).

### Integration status

The current Hep-Benchmark-Suite integration status.

- Benchmarks

Benchmark   | Docker             | Singularity
:---:       | :---:              | :---:              
HEPSpec06_32| :white_check_mark: | :white_check_mark: 
HEPSpec06_64| :white_check_mark: | :white_check_mark: 
SPEC2017    | :white_check_mark: | :white_check_mark: 
HEP-Score   | :white_check_mark: | :white_check_mark:

- Plugins

Plugin        | Status |
:---:         | :--:               |
HW-Metadata   | :white_check_mark: |
ActiveMQ      | :white_check_mark: |
Elastic Search|:x:        |


### Available benchmarks
The HEP Benchmark Suite is delivered **ready-to-run** with a [default yaml](hepbenchmarksuite/config/benchmarks.yml) configuration file (see [How to run](#how-to-run)). The  currently available benchmarks are:
- [HEP-score](https://gitlab.cern.ch/hep-benchmarks/hep-score)
- [HS06](https://w3.hepix.org/benchmarking.html)
- [SPEC CPU2017](https://www.spec.org/cpu2017/)
- Fast benchmarks (should not be used for performance measurments):
    - DIRAC Benchmark (DB12)
    - [ATLAS Kit Validation](https://gitlab.cern.ch/hep-benchmarks/hep-workloads/blob/master/atlas/kv/atlas-kv/DESCRIPTION)

**Due to proprietary license requirements, HS06 and SPEC CPU 2017 must be provided by the end user.** This tool will work with either a pre-installed or tarball archive of SPEC software.

### Example of a sparse deployment of HEP Benchmark Suite

<img src="doc/images/HEP-Benchmark-Suite-Workflow.png" width="500">

*The above figure shows an example adoption of the HEP Benchmark suite for a multi-partition deployment.*

Servers belonging to different data centres (or cloud providers) are benchmarked by executing the HEP Benchmark Suite in each of them. The mentioned servers can be *bare metal* servers as well as *virtual machines*. After running, the final JSON report is published to an AMQ message broker (*shown as transport layer above*).

In this example, an AMQ consumer may then digest the messages from the broker, and insert them in an Elasticsearch cluster so that the benchmark results can be aggregated and visualized in dashboards. Metadata (such as UID, CPU architecture, OS, Cloud name, IP address, etc.) are also included into the searchable results.

Users are free to build/use transport and aggregation/visualization tools of their choice to ingest the generated JSON results.

## Installation

**NB: This package requires pip3 >= 19.1**\
If your `pip3 --version` is older, please update with:\
`pip3 install --user --upgrade pip`

```sh
python3 -m pip install --user git+https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite.git@qa-v2.0
```
This will install the suite to the user's home directory:
```sh
~/.local/bin/bmkrun
```
You can additionally add the executible to you $PATH:
```sh
export PATH=$PATH:~/.local/bin
```

## How to run

The python executable (*bmkrun*) can be added to the user's `$PATH`, and launched directly.
Without argument, this will execute the distributed defaults as defined in `benchmarks.yml`.
Users are free to provide [command-line arguments](#description-of-all-arguments), or edit the [`benchmarks.yml`](hepbenchmarksuite/config/benchmarks.yml) file directly.

- Running the HEP Benchmark Suite using Docker containers (default)
	- `./bmkrun`
- Running using Singularity containers
	- `./bmkrun --mode=singularity`

The aggregated results of the selected benchmarks are written to the location and file defined by the `--rundir=` & `--file=` argument (defined as `/tmp/hep-spec_wd3/result_profile.json` in [`benchmarks.yml`](hepbenchmarksuite/config/benchmarks.yml)).

### Description of major arguments

In order to run a sequence of benchmarks, specify the list using the `--benchmarks` argument.
Multiple benchmarks can be executed in sequence via a single call to the hep-benchmark-suite, passing the dedicated configuration parameters. When a benchmark is not specified in the list defined by `--benchmarks`, the dedicated configuration parameters relevant to that benchmark are ignored.

In the case of running HS06, and/or SPEC CPU2017, the benchmark will look for the install at the specified `hepspec_volume:`, and if it does not exist, it will attempt to install it via tarball argument `url_tarball:`, as defined in the [`benchmarks.yml`](hepbenchmarksuite/config/benchmarks.yml)).

### Advanced Message Queuing (AMQ)

AMQ publishing is implemented using the [STOMP protocol](https://stomp.github.io/). Users must provide either a valid username/password or key/cert pair, in addition to the server and topic. The relevant section of the [config yaml](hepbenchmarksuite/config/benchmarks.yml) is given below. You can then pass the argument `--publish` to the suite.

```yaml
activemq:
  server: your-AMQ-server.com
  port: 61613
  topic: hepscore-topic
  username: user
  password: secret
  key: /path/key-file.key
  cert: /path/cert-file.pem
```


### Description of all arguments

The `-h` option provides an explanation of all command line arguments

```
$ bmkrun --help
-----------------------------------------------
High Energy Physics Benchmark Suite
-----------------------------------------------
This utility orchestrates several benchmarks

Author: Benchmarking Working Group
Contact: benchmark-suite-wg-devel@cern.ch

optional arguments:
  -h, --help            Show this help message and exit
  -b BENCHMARKS [BENCHMARKS ...], --benchmarks BENCHMARKS [BENCHMARKS ...]
                        List of benchmarks
  -c [CONFIG], --config [CONFIG]
                        Configuration file to use (yaml format)
  -d [RUNDIR], --rundir [RUNDIR]
                        Directory where benchmarks will be run
  -f [FILE], --file [FILE]
                        File to store the results
  -m [{singularity,docker}], --mode [{singularity,docker}]
                        Run benchmarks in singularity or docker containers
  -n [MP_NUM], --mp_num [MP_NUM]
                        Number of cpus to run the benchmarks
  -t [TAGS], --tags [TAGS]
                        Custom user tags
  -u [UID], --uid [UID] UID
  -p, --publish         enable reporting via AMQ credentials in YAML file
  -v, --verbose         Enables verbose mode. Display debug messages.
  --version             Show program's version number and exit
-----------------------------------------------
```

## Common Issues

1.  `pip3 install` fails due to problems with hep-score:\
    `No matching distribution found for hep-score@ git+https://gitlab.cern.ch/hep-benchmarks/hep-score.git (from hep-benchmark-suite==2.0.0)`\
    Solution: HEP Benchmark suite requires pip3 19.1 or newer. Upgrade pip with `pip3 install --user --upgrade pip`
