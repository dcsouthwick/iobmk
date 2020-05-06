#!/bin/bash -e

. $(readlink -f $(dirname $0))/config_ci_tests.sh

# Working dir must belong to bmkuser to avoid problems in docker
export SINGULARITYENV_BMK_RUNDIR=${BMK_RUNDIR}
if [[ ! -e ${BMK_VOLUME} ]]; then
    mkdir -p ${BMK_VOLUME}
fi
chown -R bmkuser ${BMK_VOLUME}

if [[ ! -e ${SPEC_DIR} ]]; then
    mkdir -p ${SPEC_DIR}
fi
chown -R bmkuser ${SPEC_DIR}

if [[ -z ${SINGULARITY_CACHEDIR} ]]; then
    export SINGULARITY_CACHEDIR=${BMK_VOLUME}/singularity_cache
fi
export SINGULARITYENV_SINGULARITY_CACHEDIR=${SINGULARITY_CACHEDIR}

# Run the benchmark with all the parameters 
su bmkuser -c "singularity exec \
              -B ${BMK_VOLUME}:${BMK_VOLUME} \
              -B ${SPEC_DIR}:${SPEC_DIR} \
              docker://$BMK_SUITE_IMAGE \
              hep-benchmark-suite --benchmarks=\"$BMKLIST\" $AMQ_ARGUMENTS $HEPSCORE_CONF $HS06_ARGUMENTS $SPEC_ARGUMENTS --mp_num=2 --tags="$METADATA_ARGUMENTS"

$CI_PROJECT_DIR/test/check_result_entry.sh "$BMKLIST" $BMK_RUNDIR/hep-benchmark-suite.out