#!/usr/bin/env bats

TESTDIR=$BATS_TEST_DIRNAME

@test "check equality of hepscore singularity and docker configs" { 
      run diff -I "container_exec:" $TESTDIR/../scripts/hepscore/hepscore_singularity.yaml $TESTDIR/../scripts/hepscore/hepscore.yaml
      echo -e "$output"
      [ "$status" -eq 0 ]
}


@test "check accessibility of WL's images" { 
      run python $TESTDIR/test_get_hepscore_WLs_images.py  $TESTDIR/../scripts/hepscore/hepscore*.yaml 
      echo -e "$output"
      [ "$status" -eq 0 ]
}
