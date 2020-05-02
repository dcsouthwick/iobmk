#!/bin/bash

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

# The RUN_VOLUME directory will include the hep-benchmark-suite running directory (${BMK_RUNDIR})
# and the singularity cache directory
# Can be changed to point to any volume and directory with enough space 
RUN_VOLUME=/tmp
[ ! -e ${RUN_VOLUME} ] && mkdir -p ${RUN_VOLUME}

# The directory ${BMK_RUNDIR} will contain all the logs and the output produced by the executed benchmarks
export BMK_RUNDIR=${RUN_VOLUME}/hep-benchmark-suite

# The directory ${BMK_RUNDIR} will contain the singularity cache
export SINGULARITY_CACHEDIR=${RUN_VOLUME}/singularity_cachedir
[ ! -e ${SINGULARITY_CACHEDIR} ] && mkdir -p ${SINGULARITY_CACHEDIR}

#####################
#--- RUN
#####################

export SINGULARITYENV_BMK_RUNDIR=${BMK_RUNDIR}
export SINGULARITYENV_SINGULARITY_CACHEDIR=${SINGULARITY_CACHEDIR}

singularity exec --hostname $HOSTNAME \
              -B ${RUN_VOLUME}:${RUN_VOLUME} \
              docker://$BMK_SUITE_IMAGE \
              hep-benchmark-suite --benchmarks=$BMK_LIST $AMQ_ARGUMENTS $HEPSCORE_CONF --tags="$METADATA_ARGUMENTS"

