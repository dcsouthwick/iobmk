#!/bin/bash

## This script runs three different HEP-score config files, available in the HEP-score repository
## in order to collect duration and score of each individual HEP-Workload

DOCKSOCK=/var/run/docker.sock
BMK_SUITE_IMAGE=gitlab-registry.cern.ch/hep-benchmarks/hep-benchmark-suite/hep-benchmark-suite-cc7:latest

BMK_LIST='hepscore'

 
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
export BMK_RUNDIR=${RUN_VOLUME}/hep-benchmark-suite


function remove_lock_file() {
#Before running, check that another lock file is not present
    if [ -e ${BMK_RUNDIR}/hep-benchmark-suite.lock ];
    then
	echo -e "\nLock file still present\n" 
	
	# Check that a docker process is still running
	IS_THERE_ANY_RUNNING_BMK_IMAGE=`docker ps -a | grep -c $BMK_SUITE_IMAGE`
	[ "$IS_THERE_ANY_RUNNING_BMK_IMAGE" != "0" ] && echo -e "\nThere are images of $BMK_SUITE_IMAGE running. Exiting" && exit 1
	
	echo -e "\nThere are not images of $BMK_SUITE_IMAGE running\n removing lock file" 
	rm -f ${BMK_RUNDIR}/hep-benchmark-suite.lock || exit 1
    fi
}

function backup_dir() {
    #Before running, copy the previous dir in another one, for backup reasons
    if [ -e ${BMK_RUNDIR} ]; then 
	newfile="${RUN_VOLUME}/hep-suite_`date +%s`".tgz 
	echo -e "\nArchiving json results in $newfile \n" 
	
	tar -cvzf ${newfile}    ${BMK_RUNDIR}/hep-benchmark-suite* \
                            ${BMK_RUNDIR}/bmk_utils/* \
                            ${BMK_RUNDIR}/bmk_run/HEPSCORE/HEPscore_*/*/*json \
                            ${BMK_RUNDIR}/bmk_run/HEPSCORE/HEPscore_*/*log \
                            ${BMK_RUNDIR}/bmk_run/HEPSCORE/hepscore_*.stdout \      
                            ${BMK_RUNDIR}/bmk_run/HEPSCORE/hepscore_result.json
    fi
    echo "--------- ls ${RUN_VOLUME}"
    ls -l ${RUN_VOLUME}/ | grep hep
}


#####################################################
####### MAIN
#####################################################


systemctl is-active docker.service ; STATUS=$?; [[ $STATUS -gt 0 ]] && echo "restart docker" && systemctl restart docker.service

remove_lock_file


for i in 2 1 0;
do

    backup_dir

    curl  https://gitlab.cern.ch/hep-benchmarks/hep-score/raw/qa/hepscore/tests/etc/parameter_scan/hepscore_conf_param_scan_${i}.yaml -o ${RUN_VOLUME}/hepscore_conf_param_scan_${i}.yaml
    
    docker run --rm  --privileged --net=host -h $(hostname) \
              -e BMK_RUNDIR=$BMK_RUNDIR  -v ${RUN_VOLUME}:${RUN_VOLUME} \
              -v $DOCKSOCK:$DOCKSOCK \
              $BMK_SUITE_IMAGE \
              hep-benchmark-suite --benchmarks=$BMK_LIST $AMQ_ARGUMENTS $METADATA_ARGUMENTS --hepscore_conf=${RUN_VOLUME}/hepscore_conf_param_scan_${i}.yaml
        
done