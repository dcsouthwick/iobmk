#!/bin/bash
DOCKSOCK=/var/run/docker.sock
BMK_SUITE_IMAGE=gitlab-registry.cern.ch/hep-benchmarks/hep-benchmark-suite/hep-benchmark-suite-cc7:latest

# DB12 is a very fast benchmark, based on python random number generation. It is used only for functional tests of the suite
BMK_LIST='DB12'

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

docker run --rm  --privileged --net=host -h $HOSTNAME \
              -v /tmp:/tmp -v $DOCKSOCK:$DOCKSOCK \
              $BMK_SUITE_IMAGE hep-benchmark-suite --benchmarks=$BMK_LIST $AMQ_ARGUMENTS $METADATA_ARGUMENTS
