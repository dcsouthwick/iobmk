#!/bin/bash

ARCH=32
START=`date`
END=`date`
. ../scripts/spec2k6/runhs06.sh

calculate_results data/spec2k6-test

#Verify the json format is correct
JSON=`echo $JSON`
python -c "import json; print json.dumps(json.loads('$JSON')); print '$JSON'"

