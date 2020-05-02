#!/bin/bash

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
export BMK_RUNDIR

#####################
#--- RUN
#####################

EXECUTABLE=$(which hep-benchmark-suite)

[ "$EXECUTABLE" == "" ] && echo "hep-benchmark-suite not available. Please install it following instructions in https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/raw/master/examples/install_hep-benchmark-suite.sh" && exit 1

$EXECUTABLE --benchmarks=$BMK_LIST $AMQ_ARGUMENTS $HEPSCORE_CONF --tags="$METADATA_ARGUMENTS"


