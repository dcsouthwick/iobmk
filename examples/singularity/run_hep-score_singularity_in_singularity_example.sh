#!/bin/bash

BMK_SUITE_IMAGE=gitlab-registry.cern.ch/hep-benchmarks/hep-benchmark-suite/hep-benchmark-suite-cc7:latest

BMK_LIST='hepscore'

#####################
#--- HEP-score Config
#####################

# Optional configuration parameter to specify a different configuration file
HEPSCORE_CONF="--hepscore_conf=/opt/hep-benchmark-suite/scripts/hepscore/hepscore_ci_singularity.yaml"
 

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
export BMK_RUNDIR

export SINGULARITY_CACHEDIR=${RUN_VOLUME}/singularity_cachedir
[ ! -e ${SINGULARITY_CACHEDIR} ] && mkdir ${SINGULARITY_CACHEDIR}

#####################
#--- RUN
#####################

SINGULARITYENV_BMK_RUNDIR=${BMK_RUNDIR}
SINGULARITYENV_SINGULARITY_CACHEDIR=${SINGULARITY_CACHEDIR}

[ ! -e ${BMK_RUNDIR} ] && mkdir -p ${BMK_RUNDIR}

singularity exec --hostname $HOSTNAME \
              -B ${RUN_VOLUME}:${RUN_VOLUME} \
              docker://$BMK_SUITE_IMAGE \
              hep-benchmark-suite --benchmarks=$BMK_LIST $AMQ_ARGUMENTS $HEPSCORE_CONF $METADATA_ARGUMENTS

