#!/usr/bin/env bats

TESTDIR=$BATS_TEST_DIRNAME
QUEUE_HOST=srv_activemq
QUEUE_PORT=61613
QUEUE_USERNAME=producer_login
QUEUE_PASSWD=producer_password
QUEUE_NAME="/queue/bmkqueue"

CODE_DIR=/opt/hep-benchmark-suite


@test "Test AMQ successful connection" {
    run python ${CODE_DIR}/pyscripts/send_queue.py --port=$QUEUE_PORT \
        --server=$QUEUE_HOST --name=$QUEUE_NAME  --username=$QUEUE_USERNAME \
        --password=$QUEUE_PASSWD --file=$TESTDIR/data/result_profile_sample.json
    echo -e "$output"
    [ "$status" -eq 0 ]
}


@test "Test AMQ wrong configuration username-password" { 
    run python ${CODE_DIR}/pyscripts/send_queue.py --port=$QUEUE_PORT \
        --server=$QUEUE_HOST --name=$QUEUE_NAME  --username=$QUEUE_USERNAME \
        --file=$TESTDIR/data/result_profile_sample.json 
    echo -e "$output" 
    [ "$status" -ne 0 ]
}   


@test "Test AMQ missing topic parameter" {
    run python ${CODE_DIR}/pyscripts/send_queue.py --port=$QUEUE_PORT \
        --server=$QUEUE_HOST --username=$QUEUE_USERNAME --password=$QUEUE_PASSWD \
        --file=$TESTDIR/data/result_profile_sample.json 
    echo -e "$output"
    [ "$status" -ne 0 ]
}


@test "Test AMQ wrong topic name" {
    run python ${CODE_DIR}/pyscripts/send_queue.py --port=$QUEUE_PORT --server=$QUEUE_HOST \
        --name=foo  --username=$QUEUE_USERNAME --password=$QUEUE_PASSWD \
        --file=$TESTDIR/data/result_profile_sample.json
    echo -e "$output"
    [ "$status" -ne 0 ]
}



@test "Generate result profile for certificate tests" {
    skip
    run genData "test amq certificate"
    echo -e "$output"
    [ "$status" -eq 0 ]
}


@test "Test wrong configuration certificate" {
    skip # Needs a certificate to be tested
    
    run python ${CODE_DIR}/pyscripts/send_queue.py --port=$QUEUE_PORT --server=$QUEUE_HOST \
        --name=$QUEUE_NAME --cert_file=$CERT_FILE  --file=$TESTDIR/data/result_profile_sample.json
    echo -e "$output"
    [ "$status" -ne 0 ]
}


@test "Test both certificate and password connection" {
    skip # Needs a certificate to be tested

    run python ${CODE_DIR}/pyscripts/send_queue.py --port=$QUEUE_PORT --server=$QUEUE_HOST \
        --name=$QUEUE_NAME --cert_file=$CERT_FILE --key_file=$KEY_FILE --username=$QUEUE_USERNAME \
        --password=$QUEUE_PASSWD --file=$TESTDIR/data/result_profile_sample.json
    echo -e "$output"
    [ "$status" -ne 0 ]
}


@test "Test successful connection" {
    skip # Needs a certificate to be tested
    
    run python ${CODE_DIR}/pyscripts/send_queue.py --port=$QUEUE_PORT --server=$QUEUE_HOST \
        --name=$QUEUE_NAME --cert_file=$CERT_FILE --key_file=$KEY_FILE \
        --file=$TESTDIR/data/result_profile_sample.json
    echo -e "$output"
    [ "$status" -eq 0 ]
}


