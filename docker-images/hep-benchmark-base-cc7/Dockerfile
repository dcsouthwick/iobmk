FROM gitlab-registry.cern.ch/linuxsupport/cc7-base:latest

RUN yum install -y \
    util-linux \	
    wget \
    git \
    screen \
    tar ; yum clean all
#workaround https://github.com/CentOS/sig-cloud-instance-images/issues/15

LABEL multi.maintainer="Domenico Giordano <domenico.giordano@cern.ch>" \
      multi.version="1.0" \
      multi.description="cc7 base image for benchmarking"


