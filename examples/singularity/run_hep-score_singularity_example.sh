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
METADATA_ARGUMENTS="--cloud=name_of_your_cloud --vo=an_aggregate  --freetext=a_tag_text --pnode=physical_node_name"


EXECUTABLE=$(which hep-benchmark-suite)

[ "$EXECUTABLE" -eq "" ] && echo "hep-benchmark-suite not available. Please install it following instructions in https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/blob/master/examples/install_hep-benchmark-suite.sh" && exit 1

hep-benchmark-suite --benchmarks=$BMK_LIST $AMQ_ARGUMENTS $HEPSCORE_CONF $METADATA_ARGUMENTS


