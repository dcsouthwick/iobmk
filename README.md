# HEP Benchmark Suite

| Branch |  QA | Master |
| -------- | -------- | -------- |
|     |  [![pipeline status](https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/badges/qa/pipeline.svg)](https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/commits/qa)     |  [![pipeline status](https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/badges/master/pipeline.svg)](https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/commits/master)     |


The HEP Benchmark Suite is a toolkit which aggregates several different benchmarks
in one single application.

It is built to comply with several use cases by allowing the users to specify
which benchmarks to run.

## Goals
1. Mimic the usage of WLCG resources for experiment workloads
   * Run representative benchmarks on VMs of the same size used by VOs
1. Allow collection of a configurable number of benchmarks
   * Compare the benchmark outcome under similar conditions  
1. Probe randomly assigned slots in a cloud cluster
   * Not knowing what the neighbor is doing
1. Have a prompt feedback about executed benchmarks
   * In production can suggest deletion and re-provisioning of underperforming VMs


## Benchmark suite architecture
![System workflow](doc/Bmk-suite.png)

The figure shows the high level architecture of the benchmark suite. The data
storage, analysis and visualization layers are purely exemplifications, as users
can opt to build/use their own transport and storage tools.  

A configurable sequence of benchmarks is executed in a VM.

At the end of the sequence, the benchmark results are organized in a JSON message
and are sent to a transport layer (currently by default it is the CERN ActiveMQ
message broker). Applications can subscribe to the transport layer in order to
consume the messages. Users can also choose not to send the benchmark results to
AMQ, running on an offline mode (see [How it works](#markdown-header-how-it-works)) for further details).

Taking the example shown in the above figure, a dedicated consumer inserts messages
in an Elasticsearch cluster, so that the benchmark results can be visualized and
aggregated in dashboards. Several metadata (such as VM UID, CPU architecture,
OS, Cloud name, IP address, etc.) are included in the result message in order to
enable aggregations.

Further detailed analysis can be performed extracting data from the storage layer.



### Available benchmarks
At the moment, the available benchmarks on the suite are:
 * HS06
 * SPEC CPU 2017
 * HEPSCORE
 * DIRAC Benchmark
 * ATLAS Kit Validation
 * Hyper-benchmark<sup>\*</sup>

It is a standalone application that expects the user to pass a list of the benchmarks to be executed (together with the other possible arguments referred in [How to run](./HowToRun.md)).


### Execution modes

#### Online vs Offline
The user has the choice, at launch time, to have the benchmark results uniquely printed in the terminal at the end of the execution. This is the _Offline_ mode and must be specified. The _Online_ mode makes the suite act like a producer, expecting
the corresponding publishing arguments in the execution call (by default AMQ
is the chosen transportation layer).
On both cases, the final structured JSON file will always be generated and
available in the execution directory (by default at _/tmp_).

<sup>\*</sup> _a pre-defined sequence of measurements and fast benchmarks: </br>
**1-min Load -> read machine&job features -> DB12 -> 1-min Load -> 1-min Load**_

