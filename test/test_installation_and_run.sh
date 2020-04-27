#!/bin/bash -e

. $(readlink -f $(dirname $0))/config_ci_tests.sh

# Install new suite
cd $CI_PROJECT_DIR
make -f Makefile all 

# Run the benchmark with all the parameters 
hep-benchmark-suite --benchmarks="$BMKLIST" $ARGUMENTS

$CI_PROJECT_DIR/test/check_result_entry.sh "$BMKLIST" $BMK_RUNDIR/hep-benchmark-suite.out