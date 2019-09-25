FROM gitlab-registry.cern.ch/linuxsupport/cc7-base:latest

MAINTAINER Domenico Giordano <domenico.giordano@cern.ch>

LABEL multi.maintainer="Domenico Giordano <domenico.giordano@cern.ch>" \
      multi.version="0.1" \
      multi.description="docker runner to shrink cvmfs and build HEP workloads containers"

RUN yum install -y \
    postfix \
    && yum clean all

RUN sed -e 's@inet_interfaces = localhost@#inet_interfaces = localhost@' -e 's@inet_protocols = all@inet_protocols = ipv4@' -i /etc/postfix/main.cf

COPY announce.sh .