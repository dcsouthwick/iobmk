#!/bin/bash

function genData(){
    INSERTTIMESTAMP=`date -u +%Y-%m-%dT%H:%M:%SZ`
    INSERTFREETEXT=$1
    cat data/result_profile_template.json | sed -e "s@_INSERTTIMESTAMP_@$INSERTTIMESTAMP@g" -e "s@_INSERTFREETEXT_@$INSERTFREETEXT@g" > data/result_profile.json
}

WORKDIR=`dirname $0`
cd $WORKDIR

echo -e "\n*******Test user-passwd authentication*******\n"
genData "test amq user-passwd"

echo -e "\n......... Test wrong configuration username-password\n"
python ../run/send_queue.py --port=61113 --server=$QUEUE_HOST --name=$QUEUE_NAME  --username=$QUEUE_USERNAME  --file=data/result_profile.json

echo -e "\n......... Test missing topic parameter\n"
python ../run/send_queue.py --port=61113 --server=$QUEUE_HOST --username=$QUEUE_USERNAME --password=$QUEUE_PASSWD   --file=data/result_profile.json

echo -e "\n......... Test wrong topic name\n"
python ../run/send_queue.py --port=61113 --server=$QUEUE_HOST --name=foo  --username=$QUEUE_USERNAME --password=$QUEUE_PASSWD   --file=data/result_profile.json

echo -e "\n......... Test successful connection\n"
python ../run/send_queue.py --port=61113 --server=$QUEUE_HOST --name=$QUEUE_NAME  --username=$QUEUE_USERNAME --password=$QUEUE_PASSWD --file=data/result_profile.json

sleep 1s

echo -e "\n*******Test certificate authentication*******\n"
genData "test amq certificate"

echo -e "\n......... Test wrong configuration certificate\n"
python ../run/send_queue.py --port=61123 --server=$QUEUE_HOST --name=$QUEUE_NAME --cert_file=$CERT_FILE  --file=data/result_profile.json

echo -e "\n......... Test both certificate and password connection\n"
python ../run/send_queue.py --port=61123 --server=$QUEUE_HOST --name=$QUEUE_NAME --cert_file=$CERT_FILE --key_file=$KEY_FILE --username=$QUEUE_USERNAME --password=$QUEUE_PASSWD --file=data/result_profile.json

sleep 1s
genData "test amq certificate"

echo -e "\n......... Test successful connection\n"
python ../run/send_queue.py --port=61123 --server=$QUEUE_HOST --name=$QUEUE_NAME --cert_file=$CERT_FILE --key_file=$KEY_FILE --file=data/result_profile.json
