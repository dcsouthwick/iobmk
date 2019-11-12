FROM gitlab-registry.cern.ch/linuxsupport/cc7-base:latest

RUN yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

RUN if [ ! -s /etc/yum.repos.d/docker-ce.repo ]; then echo "Error retrieving docker-ce.repo"; exit 1; fi

RUN yum install -y docker-ce https://linuxsoft.cern.ch/wlcg/centos7/x86_64/wlcg-repo-1.0.0-1.el7.noarch.rpm \
    HEP_OSlibs util-linux  wget git \
    screen  tar freetype perl jq unzip \ 
    && yum clean all
#workaround https://github.com/CentOS/sig-cloud-instance-images/issues/15

# install bats for bash tests
RUN cd /tmp;  wget https://github.com/bats-core/bats-core/archive/v1.1.0.zip; unzip v1.1.0.zip; cd bats-core-1.1.0; ./install.sh /usr

# install net-tools for ifconfig
RUN yum install -y net-tools yum-plugin-ovl && yum clean all #because of https://github.com/CentOS/sig-cloud-instance-images/issues/15

LABEL multi.maintainer="Domenico Giordano <domenico.giordano@cern.ch>" \
      multi.version="1.0" \
      multi.description="cc7 base image for benchmarking"


