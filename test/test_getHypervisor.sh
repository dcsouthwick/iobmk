#!/bin/bash

WORKDIR=`dirname $0`
cd $WORKDIR

echo -e "\nworking request"
res=`python ../run/getHypervisor.py --endpoint=$ENDPOINT --namespace=$NAMESPACE --user=$USER --passwd=$PASSWD 2> /dev/null`
echo "Res:" $res

echo -e "\nworking request a different host"
res=`python ../run/getHypervisor.py --endpoint=$ENDPOINT --namespace=$NAMESPACE --user=$USER --passwd=$PASSWD --host=giocc7-04 2> /dev/null`
echo "Res:" $res

echo -e "\nfailing request a different host"
res=`python ../run/getHypervisor.py --endpoint=$ENDPOINT --namespace=$NAMESPACE --user=$USER --passwd=$PASSWD --host=foo 2> /dev/null`
echo "Res:" $res

echo -e "\nfailing request missing password"
res=`python ../run/getHypervisor.py --endpoint=$ENDPOINT --namespace=$NAMESPACE --user=$USER 2> /dev/null`
echo "Res:" $res

echo -e "\nfailing request wrong password"
res=`python ../run/getHypervisor.py --endpoint=$ENDPOINT --namespace=$NAMESPACE --user=$USER  --passwd=foo 2> /dev/null`
echo "Res:" $res

echo "the script itself"
python ../run/getHypervisor.py --endpoint=$ENDPOINT --namespace=$NAMESPACE --user=$USER  --passwd=foo 
