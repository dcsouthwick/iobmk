#!/bin/bash -e

# function check_executable() {
#     EXE=$(which $1)
#     [ "$EXE" -eq "" ] && echo "Executable $1 is missing. Please install it. Exiting" && exit 1
# }

# check_executable git

echo "You are going to install the HEP Benchmark Suite.

git and make need to be already installed. Checking availability...."
git --version
echo " "
make --version
echo " "
HBStag="release-containers-v1.4"
echo -e " The tag ${HBStag} will be used.
If you prefer to use another tag, 
please check the list in https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite/-/tags
and insert it."
read -p "Insert new tag or just press enter to keep the default one: " HBStag_new

[ "${HBStag_new}" != "" ] && HBStag=$HBStag_new && echo "New tag $HBStag"

cd /tmp
git clone https://gitlab.cern.ch/hep-benchmarks/hep-benchmark-suite.git
cd hep-benchmark-suite
git fetch --all --tags --prune
echo "... checking out tag ${HBStag}"
git checkout tags/${HBStag} -b ${HBStag}
make all

echo -e "\nInstallation complete!"
