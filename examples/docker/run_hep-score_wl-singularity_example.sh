#!/bin/bash
DOCKSOCK=/var/run/docker.sock
BMK_SUITE_IMAGE=gitlab-registry.cern.ch/hep-benchmarks/hep-benchmark-suite/hep-benchmark-suite-cc7:latest


BMK_LIST='hepscore'

#####################
#--- HEP-score Config
#####################

# Optional configuration parameter to specify a different configuration file
HEPSCORE_CONF="--hepscore_conf=/opt/hep-benchmark-suite/scripts/hepscore/hepscore_singularity.yaml"
 
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
METADATA_ARGUMENTS="{\"cloud\":\"Name of your cloud\",\"free_text\":\"Free text field\",\"vo\":\"an aggregate\", \"pnode\":\"physical node name\"}"

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
              -v $DOCKSOCK:$DOCKSOCK \
              $BMK_SUITE_IMAGE \
              hep-benchmark-suite --benchmarks=$BMK_LIST $AMQ_ARGUMENTS $HEPSCORE_CONF --tags="$METADATA_ARGUMENTS"
