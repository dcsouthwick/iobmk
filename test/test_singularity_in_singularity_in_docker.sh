#!/bin/bash -e

. $(readlink -f $(dirname $0))/config_ci_tests.sh

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
