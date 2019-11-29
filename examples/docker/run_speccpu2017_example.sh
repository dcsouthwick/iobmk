#!/bin/bash
DOCKSOCK=/var/run/docker.sock
BMK_SUITE_IMAGE=gitlab-registry.cern.ch/hep-benchmarks/hep-benchmark-suite/hep-benchmark-suite-cc7:latest

# SPEC CPU2017
BMK_LIST='spec2017'

#####################
#--- SPEC CPU2017 Config
#####################

#--- Mandatory Config
# Due to proprietary license aspects, HS06 and SPEC CPU 2017 need to be pre-installed on the server.
# In the case of running HS06, and/or SPEC CPU2017, the packages are expected to be already installed in `/var/HEPSPEC`. 
# In case the packages are in another path, change the corresponding entries `--spec2017_path=`, and/or `--spec2017_path`. 
SPEC_ARGUMENTS="--spec2017_path=/var/HEPSPEC"

#--- Optional Config

# Default number of iterations is 3. If a different number of iteration should run, uncomment and change this parameter
#SPEC_ITERATIONS="--spec2017_iter=1"
 
# In order to install SPEC from a tarball that can be downloaded from a url, uncomment and fill up the following argument
#SPEC_INSTALL="--spec2017_url=****"

# In order to run a single SPEC workload and not the full list, uncomment and fill up the following argument with some of the following benchmarks: 508.namd_r, 510.parest_r, 511.povray_r, 520.omnetpp_r, 523.xalancbmk_r, 526.blender_r, 531.deepsjeng_r, 541.leela_r 
#SPEC_LIMIT_BMK="--spec2017_bmk=511.povray_r" 

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
              -v /tmp:/tmp -v /var/HEPSPEC:/var/HEPSPEC -v $DOCKSOCK:$DOCKSOCK \
              $BMK_SUITE_IMAGE hep-benchmark-suite --benchmarks=$BMK_LIST $AMQ_ARGUMENTS $SPEC_ARGUMENTS $SPEC_ITERATIONS $SPEC_INSTALL $SPEC_LIMIT_BMK $METADATA_ARGUMENTS
