function base_dependencies {
    # Check O/S version
    if [ ! -f /etc/redhat-release ]; then
	echo "ERROR! O/S is not a RedHat-based Linux system"
	echo "ERROR! This script is only supported on SLC6 and CC7"
	exit 1
    elif egrep -q "^Scientific Linux CERN SLC release 6" /etc/redhat-release; then
	export OS="slc6"
	echo "INFO: Found OS $OS"
    elif egrep -q "^CentOS Linux release 7" /etc/redhat-release; then
	export OS="cc7"
	echo "INFO: Found OS $OS"
    else
	echo "ERROR! Unknown O/S '"`more /etc/redhat-release`"'"
	echo "ERROR! This script is only supported on SLC6 and CC7"
	exit 1
    fi

    
    # Install wget 
    if ! yum list installed wget;
    then
	yum install -y wget
    fi

    # install pip
    if ! hash pip 2>/dev/null
    then
	if [ $OS == 'slc6' ]; then 
	    #Still running in SLC6, need to get pip 2.6
	    yum install -y python-setuptools
            wget https://bootstrap.pypa.io/2.6/get-pip.py
            python get-pip.py
            rm -f get-pip.py
	    [ `python --version 2>&1 | grep -ic "Python 2.6"` -gt 0 ] && pip install wheel==0.29.0 #needed because Wheel 0.30.0 dropped Python 2.6 
	else
	  # running on cc7, can use 
	    yum install -y epel-release
	    yum -y install python-pip
	fi
    fi

    # install argparse
    [ `pip list | grep argparse -c` -lt 1 ] && pip install argparse

    # Prepare dependencies for sending results to AMQ
    [[ $(locale | grep LC_ALL=) == "LC_ALL=" ]] && export LC_ALL="en_US"

    
    # Install stop and SOAPpy
    if (! pip list | grep stomp) || (! pip list | grep SOAPpy)
    then
        pip install stomp.py
        pip install SOAPpy
    fi


    # install docker-ce
    if [ $OS == 'slc6' ]; then 
	echo "FIXME: no docker installation for slc6???"
    else
	yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
	if [ ! -s /etc/yum.repos.d/docker-ce.repo ]; then 
	    echo "ERROR retrieving docker-ce.repo"; 
	    exit 1; 
	fi
	yum install -y docker-ce
    fi
}

function unixbench_dependencies {
    if ! hash gcc 2>/dev/null
    then
      yum install -y gcc
    fi
}

function hs06_dependencies {
    #needed to enable some libc libraries to run hs06
    # Check O/S version
    echo "... installing HS06 dependencies for $OS"
    if [ $OS == 'slc6' ]; then
	[[ ! `yum list installed HEP_OSlibs_SL6 2&> /dev/null` ]] && yum install -y HEP_OSlibs_SL6
    else
	[[ ! `yum list installed gcc-c++ 2&> /dev/null` ]] && yum install -y gcc-c++
	[[ ! `yum list installed glibc-devel.i686 2&> /dev/null` ]] && yum install -y glibc-devel.i686 libstdc++-devel.i686  #needed to include in centos6/7 the 32 bit libc dev package
    fi
}

function spec2017_dependencies {
    echo "... no additional dependencies for spec2017"
}

function hepscore_dependencies {
    echo "... installing hepscore"
    current_dir=`pwd`
    install_dir=/tmp/install_hepscore_`date +%s`
    echo "Downloading into directory $install_dir"
    [ ! -e $install_dir ] && mkdir -p $install_dir
    cd $install_dir
    git clone https://gitlab.cern.ch/hep-benchmarks/hep-score.git
    cd hep-score
    git fetch --all --tags --prune
    git checkout tags/v0.1 -b v0.1
    pip install .
    cd $current_dir
}
