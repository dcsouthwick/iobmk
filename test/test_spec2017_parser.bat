#!/usr/bin/env bats

TESTDIR=$BATS_TEST_DIRNAME

function test_parser(){
	 START="Mon Sep 23 18:35:20 CEST 2019"
	 END="Mon Sep 23 18:35:20 CEST 2019"
	 compute_spec2017_results $TESTDIR/data/spec2017-test
	 echo $JSON > $TESTDIR/data/validate_spec2017_results.json
	
}

@test "Test parser runs" { 
      load $TESTDIR/../scripts/spec2017/runspec2017.sh
      run test_parser
      echo -e "$output"
      [ "$status" -eq 0 ]
}



@test "Test results' json format" { 
      run $TESTDIR/../pyscripts/json-differ.py $TESTDIR/data/validate_spec2017_results.json $TESTDIR/data/validate_spec2017_results_ref.json
      echo -e "$output"
      [ "$status" -eq 0 ]
}
