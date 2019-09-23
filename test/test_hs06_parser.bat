#!/usr/bin/env bats

TESTDIR=$BATS_TEST_DIRNAME

function test_hs06_parser(){
	 ARCH=32
	 START="Mon Sep 23 18:35:20 CEST 2019"
	 END="Mon Sep 23 18:35:20 CEST 2019"
	 calculate_results $TESTDIR/data/spec2k6-test
	 echo $JSON > $TESTDIR/data/validate_hs06_results.json
	
}

@test "Test parser runs" { 
      load $TESTDIR/../scripts/spec2k6/runhs06.sh
      run test_hs06_parser
      echo -e "$output"
      [ "$status" -eq 0 ]
}



@test "Test results' json format" { 
      run $TESTDIR/../pyscripts/json-differ.py $TESTDIR/data/validate_hs06_results.json $TESTDIR/data/validate_hs06_results_ref.json
      echo -e "$output"
      [ "$status" -eq 0 ]
}
