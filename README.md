# HEP Benchmark Suite

|   QA | Master |
| --------- | -------- |
|   [![pipeline status](https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/badges/qa/pipeline.svg)](https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/commits/qa)     |  [![pipeline status](https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/badges/master/pipeline.svg)](https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/commits/master)     |


- [Goals](#goals)
- [Benchmark suite architecture](#benchmark-suite-architecture)
  * [Available benchmarks](#available-benchmarks)
  * [Example of a sparse deployment of HEP Benchmark Suite](#Example-of-a-sparse-deployment-of-HEP-Benchmark-Suite)
- [Installation](#installation)
- [How to run](#how-to-run)
  * [Description of major arguments](#description-of-major-arguments)
- [Complete arguments description](#description-of-all-arguments)

## Goals
The HEP Benchmark Suite is a toolkit which aggregates several different benchmarks
in one single application.

It is built to comply with several use cases by allowing the users to specify
which benchmarks to run.

1. Mimic the usage of WLCG resources for experiment workloads
   * Run workloads representative of the production applications running on WLCG
1. Allow collection of a configurable number of benchmarks
   * Enable performance studies on a given hardware 
1. Collect the hardware metadata and the running conditions
   * Compare the benchmark outcome under similar conditions  
1. Have a prompt feedback about executed benchmarks
   * By publishing results to a monitoring system
1. Probe randomly assigned slots in a cloud environment
   * In production can suggest deletion and re-provisioning of underperforming resources


## Benchmark suite architecture


![Benchmark Suite architectural view](doc/images/HEP-Benchmark-Suite.png)
*The figure shows the high level architecture of the benchmark suite.*


A configurable sequence of benchmarks is executed by the HEP Benchmark Suite.

After execution of all benchmarks, the benchmark results are aggregated in a single JSON document, together with the hardware metadata (CPU model, host name, Data Centre name, kernel version, etc.)

Optionally, the final report can be sent to a transport layer, to be further digested and analysed by applications that are subscribed as consumer to the transport layer.

Users can also choose not to send the benchmark results out from the running machine, just by configuring the offline mode (see [How to run](#how-to-run) for further details).

### Available benchmarks
The HEP Benchmark Suite is delivered **ready-to-run** with a provided yaml configuration file (see [How to run](#how-to-run)). The  currently available benchmarks are:
- HEP-score ([link](https://gitlab.cern.ch/hep-benchmarks/hep-score))
- HS06 ([link](https://w3.hepix.org/benchmarking.html))
- SPEC CPU2017 ([link](https://www.spec.org/cpu2017/)) 
- some fast benchmarks: 
    - DIRAC Benchmark (DB12)
    - ATLAS Kit Validation ([link](https://gitlab.cern.ch/hep-benchmarks/hep-workloads/blob/master/atlas/kv/atlas-kv/DESCRIPTION))

**Due to proprietary license requirements, HS06 and SPEC CPU 2017 must be provided by the end user.** This tool will work with either a pre-installed or tarball archive of SPEC software.

In addition the *Hyper-benchmark* configuration enables a sequence of fast benchmarks and load measurements as follow:
_**1-min Load -> read machine&job features -> DB12 -> 1-min Load -> 1-min Load**_


### Example of a sparse deployment of HEP Benchmark Suite 

<img src="doc/images/HEP-Benchmark-Suite-Workflow.png" width="500">

*The above figure shows an example adoption of the HEP Benchmark suite for a multi-partition deployment.*

Servers belonging to different data centres (or cloud providers) are benchmarked by executing the HEP Benchmark Suite in each of them. The mentioned servers can be *bare metal* servers as well as *virtual machines*. After running, the final JSON report is published to an AMQ message broker (*shown as transport layer above*).

In this example, an AMQ consumer may then digest the messages from the broker, and insert them in an Elasticsearch cluster so that the benchmark results can be aggregated and visualized in dashboards. Metadata (such as UID, CPU architecture, OS, Cloud name, IP address, etc.) are also included into the searchable results.

Users are free to build/use transport and consumer tools of their choice to ingest the generated JSON results.

## Installation 

```sh
python3 -m pip install --user git+https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite.git@qa-v2.0
```
This will install the suite to the user's home directory:
```
~/.local/bin/bmkrun
~/.local/config/benchmarks.yml
```


## How to run

The python executable (*bmkrun*) can be added to the user's `PATH`, and launched directly. 
Without argument, this will execute the distributed defaults as defined in `benchmarks.yml`. 
Users are free to provide [command-line arguments](#description-of-all-arguments), or edit the `benchmarks.yml` file directly. 

A set of examples is available in the [examples folder of this repository](https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/tree/master/examples).
- Running the HEP Benchmark Suite using Docker containers (default)
	- `./bmkrun`
- Running using Singularity containers
	- `./bmkrun --mode=singularity`
    
### Description of major arguments

In order to run a sequence of benchmarks, specify the list using the `--benchmarks` argument.
Multiple benchmarks can be executed in sequence via a single call to the hep-benchmark-suite, passing the dedicated configuration parameters. When a benchmark is not specified in the list defined by `--benchmarks`, the dedicated configuration parameters relevant to that benchmark are ignored.

**TODO:**
If publication to an AMQ broker is needed, replace the variable `AMQ_ARGUMENTS=" -o"` with the expected AMQ authentication parameters (host, port, username, password, topic)
`AMQ_ARGUMENTS="--queue_host=**** --queue_port=**** --username=**** --password=**** --topic=**** "`

In the case of running HS06, and/or SPEC CPU2017, the benchmark will look for the install at the specified `hepspec_volume:`, and if it does not exist, it will attempt to install it via tarball argument `url_tarball:`, as defined in the `benchmarks.yaml`.

### Description of all arguments

The `-h` option provides an explanation of all command line arguments

```
# bmkrun --help
usage: bmkrun [-h] [-u [UID]] [-f [FILE]] [-d [RUNDIR]] [-n [MP_NUM]] [-t [TAGS]] [-b BENCHMARKS [BENCHMARKS ...]]
              [-m [{singularity,docker}]] [-c [CONFIG]]

----------------------------------------------------------------------
 bmkrun cli allows you to run several benchmarks
----------------------------------------------------------------------
Author: Benchmarking Working Group
Contact: benchmark-suite-wg-devel@cern.ch

optional arguments:
  -h, --help            show this help message and exit
  -u [UID], --uid [UID]
                        UID
  -f [FILE], --file [FILE]
                        File to store the results
  -d [RUNDIR], --rundir [RUNDIR]
                        Directory where benchmarks will be run
  -n [MP_NUM], --mp_num [MP_NUM]
                        Number of cpus to run the benchmarks
  -t [TAGS], --tags [TAGS]
                        Custom user tags
  -b BENCHMARKS [BENCHMARKS ...], --benchmarks BENCHMARKS [BENCHMARKS ...]
                        List of benchmarks
  -m [{singularity,docker}], --mode [{singularity,docker}]
                        Run benchmarks in singularity or docker containers
  -c [CONFIG], --config [CONFIG]
                        Configuration file to use (yaml format)

----------------------------------------------------------------------
```
