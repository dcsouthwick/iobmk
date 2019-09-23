FROM gitlab-registry.cern.ch/linuxsupport/slc6-base:latest

RUN yum install -y https://linuxsoft.cern.ch/wlcg/sl6/x86_64/wlcg-repo-1.0.0-1.el6.noarch.rpm \
    HEP_OSlibs_SL6 util-linux  wget git \
    screen  tar freetype perl jq; yum clean all
#workaround https://github.com/CentOS/sig-cloud-instance-images/issues/15

LABEL multi.maintainer="Domenico Giordano <domenico.giordano@cern.ch>" \
      multi.version="1.0" \
      multi.description="slc6 base image for benchmarking"


