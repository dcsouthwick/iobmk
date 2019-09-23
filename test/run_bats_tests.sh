#!/bin/bash

BASEDIR=$(readlink -f $(dirname $0))
for afile in `ls $BASEDIR/*bat`;
do
    echo -e "\nRunning tests in $afile"
    bats $afile
    [[ "$?" != "0" ]] && exit 1
done
exit 0
