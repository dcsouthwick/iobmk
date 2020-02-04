FROM gitlab-registry.cern.ch/linuxsupport/cc7-base:latest

RUN yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

RUN if [ ! -s /etc/yum.repos.d/docker-ce.repo ]; then echo "Error retrieving docker-ce.repo"; exit 1; fi

RUN yum install -y docker-ce https://linuxsoft.cern.ch/wlcg/centos7/x86_64/wlcg-repo-1.0.0-1.el7.noarch.rpm \
    HEP_OSlibs util-linux  wget git \
    screen  tar freetype perl jq unzip \
    net-tools yum-plugin-ovl python-pip \ 
    skopeo \ 
    && yum clean all
#workaround https://github.com/CentOS/sig-cloud-instance-images/issues/15
# install net-tools for ifconfig

# install bats for bash tests
RUN cd /tmp;  wget https://github.com/bats-core/bats-core/archive/v1.1.0.zip; unzip v1.1.0.zip; cd bats-core-1.1.0; ./install.sh /usr

RUN pip install dictdiffer pyyaml stomp.py

# Temporarely force a specific old version 3.2.1 of Singularity to resolve BMK-253
# (latest version is 3.4.2, a fix for this issue should appear in 3.4.3)
RUN rpm --import https://repo.opensciencegrid.org/osg/3.4/RPM-GPG-KEY-OSG
RUN yum install -y https://repo.opensciencegrid.org/osg/3.4/el7/release/x86_64/singularity-3.2.1-1.1.osg34.el7.x86_64.rpm && yum clean all

LABEL multi.maintainer="Domenico Giordano <domenico.giordano@cern.ch>" \
      multi.version="1.0" \
      multi.description="cc7 base image for benchmarking"


