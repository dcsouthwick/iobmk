#!/usr/bin/env bats

TESTDIR=$BATS_TEST_DIRNAME


function test_parser_run(){
    export BENCHMARK_TARGET=machine
    export init_tests=1506953393
    export init_kv_test=1506953393
    export end_kv_test=1506953398
    export end_tests=1506954182
    
    export DB12=18.7500457765
    export HWINFO=i6_2_f6m61s2_mhz2194.916
    
    export HYPER_BENCHMARK=1
    export HYPER_1minLoad_1=1.1
    export HYPER_1minLoad_2=1.1
    export HYPER_1minLoad_3=1.1
    
    python $TESTDIR/../pyscripts/parser.py -i f2429109a5a6_a1842eb2-06a5-4ba9-87c8-86ca0f2c49b3 --mp_num=2 --tags='{"cloud":"suite-CI","pnode":"abcd","free_text":"some free text","name":"mymachine","vo":"foo"}' -f $TESTDIR/data/result_profile.json -p 172.17.0.2 -d $TESTDIR/data/bmk_run -n "mymachine"
}


@test "Test parser runs" { 
    run test_parser_run
    echo -e "$output"
    [ "$status" -eq 0 ]
}


@test "Test results' json format" { 
    # Need to exclude a list of host data because computed at runtime and potentially different in each CI    
    run $TESTDIR/../pyscripts/json-differ.py $TESTDIR/data/validate_result_profile_ref.json $TESTDIR/data/result_profile.json '["host.SW", "host.HW"]'
    echo -e "$output"
    [ "$status" -eq 0 ]
}


# Test that the printout is generated 
function test_print_results(){
    cd $TESTDIR/..
    python -c "from pyscripts import parser; parser.print_results_from_file(\"$TESTDIR/data/validate_result_profile_ref.json\")" > $TESTDIR/data/validate_print_results
    diff $TESTDIR/data/validate_print_results $TESTDIR/data/validate_print_results_ref
    return $?
}


@test "Test parser printout matches ref file" { 
    run test_print_results
    echo -e "$output"
    [ "$status" -eq 0 ]
}

# Test the check_result_entry.sh
@test "Test the functioning check_result_entry.sh" { 
    run $TESTDIR/check_result_entry.sh "DB12;kv;hepscore;hs06_32;hs06_64;spec2017" $TESTDIR/data/validate_print_results_ref
    echo -e "$output"
    [ "$status" -eq 0 ]
}
