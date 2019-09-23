#!/bin/bash

#test the download, installation and run of the HS06 and SPEC2017
#_specify_ env variables HS06URL SPEC2017URL

cern-benchmark --benchmarks="spec2017;hs06_32" --freetext="install spec2017"  --cloud=$CLOUD --vo="suite-CI" -o -d --spec2017_path=/var/spec2017 --spec2017_iter=1  --spec2017_bmk=511.povray_r --hs06_path=/var/hs06 --hs06_iter=1 --hs06_bmk=453.povray  --hs06_url=$HS06URL  --spec2017_url=$SPEC2017URL


