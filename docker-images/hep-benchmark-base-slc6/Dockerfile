FROM gitlab-registry.cern.ch/linuxsupport/slc6-base:latest

RUN yum install -y \
    HEP_OSlibs_SL6 \ # was: http://linuxsoft.cern.ch/wlcg/sl6/x86_64/HEP_OSlibs_SL6-1.0.19-0.el6.x86_64.rpm \
    util-linux \	
    wget \
    git \
    screen \
    tar ; yum clean all
#workaround https://github.com/CentOS/sig-cloud-instance-images/issues/15

LABEL multi.maintainer="Domenico Giordano <domenico.giordano@cern.ch>" \
      multi.version="1.0" \
      multi.description="slc6 base image for benchmarking"


