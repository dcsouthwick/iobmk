#!/bin/bash -e

. $(readlink -f $(dirname $0))/config_ci_tests.sh

# Working dir must belong to bmkuser to avoid problems in docker
SINGULARITYENV_BMK_RUNDIR=${BMK_RUNDIR}
if [[ ! -e ${BMK_VOLUME} ]]; then
    su bmkuser -c "mkdir -p ${BMK_VOLUME}"
else
    chown -R bmkuser ${BMK_VOLUME}
fi

if [[ -z ${SINGULARITY_CACHEDIR} ]]; then
    export SINGULARITY_CACHEDIR=${BMK_VOLUME}/singularity_cache
fi
export SINGULARITYENV_SINGULARITY_CACHEDIR=${SINGULARITY_CACHEDIR}

# Run the benchmark with all the parameters 
su bmkuser -c "singularity exec \
              -B ${BMK_VOLUME}:${BMK_VOLUME} \
              docker://$BMK_SUITE_IMAGE \
              hep-benchmark-suite --benchmarks=\"$BMKLIST\" $ARGUMENTS"


$CI_PROJECT_DIR/test/check_result_entry.sh "$BMKLIST" $BMK_RUNDIR/hep-benchmark-suite.out
