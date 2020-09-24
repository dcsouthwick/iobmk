#!/bin/bash -e

# This script is used by the gitlab CI of this repository to run a 
# test of insertion of anomaly results, in JSON format into an ElasticSearch instance
# using fluentd as transport system
# Requirements:
# 
# In order to run the same script manually, assuming only docker available, run
#
# docker run --rm -v /tmp:/tmp -v /builds:/builds -v `pwd`:`pwd` -w `pwd` \
#      -v /var/run/docker.sock:/var/run/docker.sock gitlab-registry.cern.ch/cloud-infrastructure/data-analytics/compose:qa sh -c ". ./ci_run_script.sh; start_docker_compose; run_reader; stop_docker_compose"

function start_docker_compose() {
    cd $WORK_DIR
    ls -l
    rm -f compose.log

    #Use docker-compose variable substitution as from
    #https://docs.docker.com/compose/compose-file/#variable-substitution

    docker-compose -f docker-compose.yml -p amq_to_es_${CI_COMMIT_SHORT_SHA} down --remove-orphans --volumes 
 
    #sleep 5
    docker-compose -f docker-compose.yml -p amq_to_es_${CI_COMMIT_SHORT_SHA} up --remove-orphans --abort-on-container-exit >> compose.log &
    #docker-compose logs -f 2>&1 >> compose.log &
    docker ps
}

function run_amq_bats_test() {
    # go to main project dir
    this_work_dir=$CI_PROJECT_DIR
    sleep 30s
    docker run --rm --net=amq_to_es_${CI_COMMIT_SHORT_SHA}_default --name mytester_write -v $this_work_dir:$this_work_dir -w $this_work_dir ${CI_REGISTRY_IMAGE}/hep-benchmark-suite-cc7:latest bats tests/qa_send_queue.bat
}

function run_es_reader() {
    docker run --rm --net=amq_to_es_${CI_COMMIT_SHORT_SHA}_default --name mytester_reader \
        -v $this_work_dir:$this_work_dir -w $this_work_dir ${CI_REGISTRY_IMAGE}/es-extractor:latest \
        python3 $WORK_DIR/query_es.py --url=${es_url} --username=${es_username}\
             --password=${es_passwd} --port=${es_port} --index=${es_index} --request=${request_file} \
             --output_file=${es_outfile} --ref_file=${ref_file} --force #--verify_certs --ca_certs='/etc/pki/tls/certs/ca-bundle.trust.crt'
}

function conf_hepscore() {
    es_index=bmkwg-prod-hepscore-v2.0-dev
    es_outfile=$WORK_DIR/hepscore_output.json
    ref_file=${WORK_DIR}/es_conf/ref_hepscore_output.json
}

function conf_summary() {
    es_index=bmkwg-prod-summary-v2.0-dev
    es_outfile=$WORK_DIR/summary_output.json
    ref_file=${WORK_DIR}/es_conf/ref_summary_output.json
}

function run_reader() {
    this_work_dir=$CI_PROJECT_DIR/tests/
    es_url="http://srv_elasticsearch"
    es_port=9200
    es_username=myelastic
    es_passwd=mypass
    request_file=$WORK_DIR/es_conf/es_query.json

    conf_hepscore
    run_es_reader

    conf_summary
    run_es_reader

}

function stop_docker_compose(){
    cd $WORK_DIR
    docker-compose -f docker-compose.yml -p amq_to_es_${CI_COMMIT_SHORT_SHA} down --remove-orphans --volumes 

    echo "Dump docker compose log"
    cat compose.log

    if [ `docker ps -a --filter "name=srv_.*_${CI_COMMIT_SHORT_SHA}" | cut -d " " -f1 | grep -v CONTAINER -c` -gt 0 ]; then
        docker ps -a --filter "name=srv_.*_${CI_COMMIT_SHORT_SHA}" | cut -d " " -f1 | grep -v CONTAINER | xargs docker rm -f
    fi

    sleep 10
    docker network rm amq_to_es_${CI_COMMIT_SHORT_SHA}_default || echo 'this command failed'
    docker volume rm -f amq_to_es_${CI_COMMIT_SHORT_SHA}_esdata66 || echo 'this command failed'
}

export WORK_DIR=$(readlink -f $(dirname $BASH_SOURCE))
echo WORK_DIR $WORK_DIR

export CI_REGISTRY_IMAGE=gitlab-registry.cern.ch/hep-benchmarks/hep-benchmark-suite
export CI_PROJECT_DIR=${CI_PROJECT_DIR:-"${WORK_DIR}/../.."}
export CI_COMMIT_BRANCH=${CI_COMMIT_BRANCH:-qa}
export CI_COMMIT_TAG=${CI_COMMIT_TAG:-$CI_COMMIT_BRANCH}
export CI_COMMIT_SHORT_SHA=${CI_COMMIT_SHORT_SHA:-0000}

echo CI_PROJECT_DIR $CI_PROJECT_DIR
echo CI_COMMIT_BRANCH $CI_COMMIT_BRANCH
echo CI_COMMIT_SHORT_SHA ${CI_COMMIT_SHORT_SHA}