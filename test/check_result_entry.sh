#!/bin/bash
# Script to test in the CI that a specific benchmark produced the expected output

BMKLIST=$1
TESTFILE=$2

function find_token(){
    token=$1
    echo -e "Looking for result entry for benchmark $bmk"
    COUNTS=$(grep -c "$1" $TESTFILE)
    if [ "$COUNTS" == "0" ]; then
	echo -e "ERROR: token '$token' for benchmark $bmk not found in $TESTFILE"
	exit 1
    fi
}

echo -e "List of benchmarks to check $BMKLIST"
echo -e "File to test $TESTFILE"

for bmk in ${BMKLIST//;/ }
do 
    [ "$bmk" == "kv" ] && find_token "KV cpu performance \[evt/sec\]"
    [ "$bmk" == "DB12" ] && find_token "DIRAC Benchmark ="
    [ "$bmk" == "hs06_32" ] && find_token "HS06 32 bit Benchmark ="
    [ "$bmk" == "hs06_64" ] && find_token "HS06 64 bit Benchmark ="
    [ "$bmk" == "spec2017" ] && find_token "SPEC2017 64 bit Benchmark ="
    [ "$bmk" == "hepscore" ] && find_token "HEPSCORE Benchmark ="
done
exit 0
