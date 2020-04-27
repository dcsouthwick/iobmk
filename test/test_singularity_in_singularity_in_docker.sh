#!/bin/bash -e

BMK_SUITE_IMAGE=gitlab-registry.cern.ch/hep-benchmarks/hep-benchmark-suite/hep-benchmark-suite-cc7:qa
BMK_LIST='hepscore'
HEPSCORE_CONF="--hepscore_conf=/opt/hep-benchmark-suite/scripts/hepscore/hepscore_ci_singularity.yaml"
AMQ_ARGUMENTS=" -o"


if [[ -z ${CI_PROJECT_DIR} ]]; then
    echo "CI_PROJECT_DIR is not defined. Defining fake params"
    export CI_PROJECT_DIR=$(readlink -f $(dirname $0))/..
    export CI_JOB_NAME="local_test"
    export CI_JOB_ID="noid"
    export CI_COMMIT_SHA='nocommit'
    env | grep "CI_"
fi

[[ -z ${BMK_RUNDIR} ]] && export BMK_RUNDIR=/tmp/${CI_JOB_NAME}_${CI_JOB_ID}
echo "BMK_RUNDIR $BMK_RUNDIR"

[[ -z ${BMK_HEPSCORE_CONF} ]] &&  export BMK_HEPSCORE_CONF=/opt/hep-benchmark-suite/scripts/hepscore/hepscore_ci_singularity.yaml
[[ -z ${AMQ_ARGUMENTS} ]] && export AMQ_ARGUMENTS="-o"

if [[ ! -z ${HS06URL} ]]; then
    HS06_PATH="--hs06_path=/scratch/HEPSPEC"
    HS06_ITERATIONS="--hs06_iter=1"
    HS06_INSTALL="--hs06_url=$HS06URL"
    HS06_LIMIT_BMK="--hs06_bmk=453.povray"
fi
HS06_ARGUMENTS=`echo "$HS06_PATH $HS06_ITERATIONS $HS06_INSTALL $HS06_LIMIT_BMK"`

if [[ ! -z ${SPEC2017URL} ]]; then
    SPEC_PATH="--spec2017_path=/scratch/HEPSPEC"
    SPEC_ITERATIONS="--spec2017_iter=1"
    SPEC_INSTALL="--spec2017_url=$SPEC2017URL"
    SPEC_LIMIT_BMK="--spec2017_bmk=511.povray_r"
fi
SPEC_ARGUMENTS=`echo "$SPEC_PATH $SPEC_ITERATIONS $SPEC_INSTALL $SPEC_LIMIT_BMK"`

FREETEXT="test $CI_COMMIT_BRANCH $BMKLIST version ${CI_COMMIT_SHA:0:8}" 
METADATA_ARGUMENTS="--mp_num=2 --cloud='suite-CI' --vo='suite-CI'  --freetext=\"$FREETEXT\""

ARGUMENTS=`echo "$AMQ_ARGUMENTS $HEPSCORE_CONF $HS06_ARGUMENTS $SPEC_ARGUMENTS $METADATA_ARGUMENTS"`

# Working dir must belong to bmkuser to avoid problems in docker
SINGULARITYENV_BMK_RUNDIR=${BMK_RUNDIR}
if [[ ! -e ${BMK_RUNDIR} ]]; then
    su bmkuser -c "mkdir -p ${BMK_RUNDIR}"
else
    chown -R bmkuser ${BMK_RUNDIR}
fi

if [[ -z ${SINGULARITY_CACHEDIR} ]]; then
    export SINGULARITY_CACHEDIR=/tmp/${CI_JOB_NAME}_${CI_JOB_ID}_singularity_cache
fi
SINGULARITYENV_SINGULARITY_CACHEDIR=${SINGULARITY_CACHEDIR}

# Run the benchmark with all the parameters 
su bmkuser -c "singularity exec \
              -B ${BMK_RUNDIR}:${BMK_RUNDIR} \
              docker://$BMK_SUITE_IMAGE \
              hep-benchmark-suite --benchmarks=\"$BMKLIST\" $ARGUMENTS"


$CI_PROJECT_DIR/test/check_result_entry.sh "$BMKLIST" $BMK_RUNDIR/hep-benchmark-suite.out
