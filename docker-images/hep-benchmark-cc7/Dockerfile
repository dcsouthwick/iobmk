FROM gitlab-registry.cern.ch/hep-benchmarks/hep-benchmark-suite/hep-benchmark-suite-base-cc7:latest

COPY . /to_be_installed

LABEL multi.maintainer="Domenico Giordano <domenico.giordano@cern.ch>" \
      multi.version="0.1" \
      multi.description="container of the full suite"

RUN yum install -y yum-plugin-ovl #because of https://github.com/CentOS/sig-cloud-instance-images/issues/15
RUN groupadd bmkuser 
RUN useradd -g bmkuser --create-home --shell /bin/bash bmkuser
RUN cd /to_be_installed ; make all; rm -rf /to_be_installed

