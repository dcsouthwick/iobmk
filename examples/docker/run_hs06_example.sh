#!/bin/bash
DOCKSOCK=/var/run/docker.sock
BMK_SUITE_IMAGE=gitlab-registry.cern.ch/hep-benchmarks/hep-benchmark-suite/hep-benchmark-suite-cc7:latest

# HS06 runs built at 32 and/or 64 bits
BMK_LIST='hs06_32;hs06_64'

#####################
#--- HS06 Config
#####################

#--- Mandatory Config
# Due to proprietary license aspects, HS06 and SPEC CPU 2017 need to be pre-installed on the server.
# In the case of running HS06, and/or SPEC CPU2017, the packages are expected to be already installed in `/var/HEPSPEC`. 
# In case the packages are in another path, change the corresponding entries `--hs06_path=`, and/or `--spec2017_path`. 
SPEC_DIR="/var/HEPSPEC"
HS06_ARGUMENTS="--hs06_path=${SPEC_DIR}"

#--- Optional Config

# Default number of iterations is 3. If a different number of iteration should run, uncomment and change this parameter
#HS06_ITERATIONS="--hs06_iter=1"
 
# In order to install HS06 from a tarball that can be downloaded from a url, uncomment and fill up the following argument
#HS06_INSTALL="--hs06_url=****"

# In order to run a single HS06 workload and not the full list, uncomment and fill up the following argument with some of the following benchmarks: 450.soplex, 471.omnetpp, 447.dealII, 473.astar, 444.namd, 453.povray, 483.xalancbmk
#HS06_LIMIT_BMK="--hs06_bmk=453.povray" 

#####################
#--- AMQ Config
#####################

AMQ_ARGUMENTS=" -o"
# In order to publish in AMQ broker, uncomment and fill up the following arguments
#AMQ_ARGUMENTS="--queue_host=**** --queue_port=**** --username=**** --password=**** --topic=****"

#####################
#--- Metadata Config
#####################

# Those metadata are not mandatory
METADATA_ARGUMENTS="--cloud=name_of_your_cloud --vo=an_aggregate  --freetext=a_tag_text --pnode=physical_node_name"

#####################
#--- WORKING DIR
#####################

# The directory ${BMK_RUNDIR} will contain all the logs and the output produced by the executed benchmarks
# Can be changed to point to any volume and directory with enough space 
RUN_VOLUME=/tmp
BMK_RUNDIR=${RUN_VOLUME}/hep-benchmark-suite

#####################
#--- RUN
#####################

docker run --rm  --privileged --net=host -h $HOSTNAME \
              -e BMK_RUNDIR=$BMK_RUNDIR  -v ${RUN_VOLUME}:${RUN_VOLUME} \
              -v ${SPEC_DIR}:${SPEC_DIR} \
              -v $DOCKSOCK:$DOCKSOCK \
              $BMK_SUITE_IMAGE \
              hep-benchmark-suite --benchmarks=$BMK_LIST $AMQ_ARGUMENTS $HS06_ARGUMENTS $HS06_ITERATIONS $HS06_INSTALL $HS06_LIMIT_BMK $METADATA_ARGUMENTS
