#!/usr/bin/env bats

TESTDIR=$BATS_TEST_DIRNAME

function genData(){
    INSERTTIMESTAMP=`date -u +%Y-%m-%dT%H:%M:%SZ`
    INSERTFREETEXT=$1
    cd $TESTDIR
    cat data/result_profile_template.json | sed -e "s@_INSERTTIMESTAMP_@$INSERTTIMESTAMP@g" -e "s@_INSERTFREETEXT_@$INSERTFREETEXT@g" > data/result_profile.json
}

@test "Generate result profile for the next tests" {
    run genData "test amq user-passwd"
    echo -e "$output"
    [ "$status" -eq 0 ]
}
@test "Test AMQ wrong configuration username-password" { 
    run python $TESTDIR/../pyscripts/send_queue.py --port=61113 --server=$QUEUE_HOST --name=$QUEUE_NAME  --username=$QUEUE_USERNAME  --file=$TESTDIR/data/result_profile.json 
    echo -e "$output" 
    [ "$status" -ne 0 ]
}   


@test "Test AMQ missing topic parameter" {
    run python $TESTDIR/../pyscripts/send_queue.py --port=61113 --server=$QUEUE_HOST --username=$QUEUE_USERNAME --password=$QUEUE_PASSWD   --file=$TESTDIR/data/result_profile.json 
    echo -e "$output"
    [ "$status" -ne 0 ]
}


@test "Test AMQ wrong topic name" {
    run python $TESTDIR/../pyscripts/send_queue.py --port=61113 --server=$QUEUE_HOST --name=foo  --username=$QUEUE_USERNAME --password=$QUEUE_PASSWD   --file=$TESTDIR/data/result_profile.json
    echo -e "$output"
    [ "$status" -ne 0 ]
}


@test "Test AMQ successful connection" {
    run python $TESTDIR/../pyscripts/send_queue.py --port=61113 --server=$QUEUE_HOST --name=$QUEUE_NAME  --username=$QUEUE_USERNAME --password=$QUEUE_PASSWD --file=$TESTDIR/data/result_profile.json
    echo -e "$output"
    [ "$status" -eq 0 ]
}


@test "Generate result profile for certificate tests" {
    run genData "test amq certificate"
    echo -e "$output"
    [ "$status" -eq 0 ]
}


@test "Test wrong configuration certificate" {
    skip # Needs a certificate to be tested
    
    run python $TESTDIR/../pyscripts/send_queue.py --port=61123 --server=$QUEUE_HOST --name=$QUEUE_NAME --cert_file=$CERT_FILE  --file=$TESTDIR/data/result_profile.json
    echo -e "$output"
    [ "$status" -ne 0 ]
}


@test "Test both certificate and password connection" {
    skip # Needs a certificate to be tested

    run python $TESTDIR/../pyscripts/send_queue.py --port=61123 --server=$QUEUE_HOST --name=$QUEUE_NAME --cert_file=$CERT_FILE --key_file=$KEY_FILE --username=$QUEUE_USERNAME --password=$QUEUE_PASSWD --file=$TESTDIR/data/result_profile.json
    echo -e "$output"
    [ "$status" -ne 0 ]
}


@test "Test successful connection" {
    skip # Needs a certificate to be tested
    
    run python $TESTDIR/../pyscripts/send_queue.py --port=61123 --server=$QUEUE_HOST --name=$QUEUE_NAME --cert_file=$CERT_FILE --key_file=$KEY_FILE --file=$TESTDIR/data/result_profile.json
    echo -e "$output"
    [ "$status" -eq 0 ]
}

