#!/bin/bash

START=`date`
END=`date`
. ../lib/spec2017/runspec2017.sh

set +x
compute_spec2017_results data/spec2017-test

#Verify the json format is correct
JSON=`echo $JSON` #this removes spaces and line break
python -c "import json; print json.dumps(json.loads('$JSON'))"

