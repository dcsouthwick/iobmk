#!/bin/bash
IMAGE=$1
postfix start
announcement="announce.txt"
echo -e "Dear, \n" > $announcement
echo -e "we are pleased to inform that a new version has been released for the container image \n\n${IMAGE}" >> $announcement
echo -e "\nCOMMIT DESCRIPTION $CI_COMMIT_DESCRIPTION" >> $announcement
echo -e "\nPlease DO NOT REPLY\nReport automatically generated from GitLab CI in pipeline ${CI_PIPELINE_URL}\n[$(date)]" >> $announcement
echo -e "\nYours sincerely,\nHEPiX Benchmarking Working Group\n\n" >> $announcement
cat $announcement
cat $announcement | mail -r ${CI_MAIL_FROM} -s "hep-benchmark-suite: New Docker container available $IMAGE" ${CI_ANNOUNCE_TO}
sleep 100s # keep the container alive, otherwise no email is sent (emails are sent only once per minute, see BMK-80)
