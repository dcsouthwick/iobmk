#!/bin/bash -e

if [[ -z ${CI_PROJECT_DIR} ]]; then
    echo "CI_PROJECT_DIR is not defined. Defining fake params"
    export CI_PROJECT_DIR=$(readlink -f $(dirname $0))/..
    export CI_JOB_NAME="local_test"
    export CI_JOB_ID="noid"
    export CI_COMMIT_SHA='nocommit'
    env | grep "CI_"
else 
    echo "CI_PROJECT_DIR=${CI_PROJECT_DIR}"
fi

[[ -z ${BMK_VOLUME} ]] && export BMK_VOLUME=/tmp/${CI_JOB_NAME}_${CI_JOB_ID} && export BMK_RUNDIR=${BMK_VOLUME}/hep-benchmark-suite
echo "BMK_VOLUME $BMK_VOLUME"
echo "BMK_RUNDIR $BMK_RUNDIR"

[[ -z ${BMK_HEPSCORE_CONF} ]] &&  export BMK_HEPSCORE_CONF=/opt/hep-benchmark-suite/scripts/hepscore/hepscore_ci_singularity.yaml
echo "BMK_HEPSCORE_CONF=${BMK_HEPSCORE_CONF}"
export HEPSCORE_CONF="--hepscore_conf=${BMK_HEPSCORE_CONF}"

[[ -z ${AMQ_ARGUMENTS} ]] && export AMQ_ARGUMENTS="-o" && echo "running with offline AMQ_ARGUMENTS"

[[ -z ${SPEC_DIR} ]] && SPEC_DIR=/scratch/HEPSPEC
if [[ ! -z ${HS06URL} ]]; then
    HS06_PATH="--hs06_path=${SPEC_DIR}"
    HS06_ITERATIONS="--hs06_iter=1"
    HS06_INSTALL="--hs06_url=$HS06URL"
    HS06_LIMIT_BMK="--hs06_bmk=453.povray"
fi
export HS06_ARGUMENTS=`echo "$HS06_PATH $HS06_ITERATIONS $HS06_INSTALL $HS06_LIMIT_BMK"`

if [[ ! -z ${SPEC2017URL} ]]; then
    SPEC_PATH="--spec2017_path=${SPEC_DIR}"
    SPEC_ITERATIONS="--spec2017_iter=1"
    SPEC_INSTALL="--spec2017_url=$SPEC2017URL"
    SPEC_LIMIT_BMK="--spec2017_bmk=511.povray_r"
fi
export SPEC_ARGUMENTS=`echo "$SPEC_PATH $SPEC_ITERATIONS $SPEC_INSTALL $SPEC_LIMIT_BMK"`

[[ -z ${METADATA_ARGUMENTS} ]] && METADATA_ARGUMENTS="{\"cloud\":\"suite-CI\",\"free_text\":\"test $CI_COMMIT_BRANCH $BMKLIST version ${CI_COMMIT_SHA:0:8}\",\"vo\":\"suite-CI\"}"


