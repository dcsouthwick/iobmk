#
#  Copyright (c) CERN 2016
#
#  Author: Cristovao Cordeiro
# 

# Help display
usage='Usage:
 $0 [OPTIONS]

OPTIONS:
-d\t debug verbosity
-q\t Quiet mode. Do not prompt user
-o\t Offline mode. Do not publish results. If not used, the script expects the publishing parameters
--benchmarks=<bmk1;bmk2>
\t (REQUIRED) Semi-colon separated list of benchmarks to run. Available benchmarks are:
\t\t - hs06_32 (for 32 bits)
\t\t - hs06_64 (for 64 bits)
\t\t - spec2017
\t\t - hepscore
\t\t - kv
\t\t - DB12
\t\t - hyper-benchmark (*)
--mp_num=#
\t Number of concurrent processes (usually cores) to run. If not used, mp_num = cpu_num
--uid=<id>
\t (Optional) Unique identifier for the host running this script. If not specified, it will be generated
--public_ip=<ip>
\t (Optional) Public IP address of the host running this script. If not specified, it will be generated
--cloud=<cloudName>
\t Cloud name to identify the results - if not specified, CLOUD=test and use -q to avoid prompt
--vo=<VO>
\t (Optional) Name of the VO responsible for the underlying resource
--pnode=<physicalNode>
\t (Optional) Name of the hypervisor machine hosting the VM
--queue_port=<portNumber>
\t Port number of the ActiveMQ broker where to send the benchmarking results
--queue_host=<hostname>
\t Hostname with the ActiveMQ broker where to send the benchmarking results
--username=<username>
\t Username to access the ActiveMQ broker where to send the benchmarking results
--password=<password>
\t User password to access ActiveMQ broker where to send the benchmarking results
--amq_key=<path_to_key>
\t Key file for the AMQ authentication, without passphrase. Expects --amq_cert
--amq_cert=<path_to_cert>
\t Certificate for the AMQ authentication. Expects --amq_key
--topic=<topicName>
\t Topic (or Queue) name used in the ActiveMQ broker
--freetext=<string>
\t (Optional) Any additional free text to add to the generated output JSON
\t (*) this benchmark performs the following measurements sequence: 1-min Load -> read machine&job features -> DB12 -> 1-min Load -
--hs06_path=<string>
\t MANDATORY: Path where the HEPSPEC06 installation is expected 
--hs06_url=<string>
\t url where the HEPSPEC06 tarball is expected to be downloaded. The tarball is then unpacked into hs06_path 
--hs06_bmk=<string>
\t the hs06 benchmark otherwise the default (all_cpp) is used. Example --hs06_bmk=453.povray 
--hs06_iter=<string>
\t the hs06 number of iterations for each benchmark in the HS06 suite. Default is 3
--spec2017_path=<string>
\t MANDATORY: Path where the HEPSPEC06 installation is expected 
--spec2017_url=<string>
\t url where the HEPSPEC06 tarball is expected to be downloaded. The tarball is then unpacked into spec2017_path 
--spec2017_bmk=<string>
\t the spec2017 benchmark otherwise the default (pure_rate_cpp) is used. Example --spec2017_bmk=511.povray_r 
--spec2017_iter=<string>
\t the spec2017 number of iterations for each benchmark in the SPEC2017 suite. Default is 3
'

# Execution Directory
DIRNAME=`readlink -m ${BMK_LOGDIR:-"/tmp/$(basename $0)_$(whoami)"}`

LOG="$DIRNAME/$(basename $0).out"
LOCK_FILE="$DIRNAME/$(basename $0).lock"
END=0

# If the script is running exit
if [ -e $LOCK_FILE ]; then
 echo "Exiting because of $0 already running. $LOCK_FILE exists and last time modified: $(stat -c %y $LOCK_FILE)"
 exit 0
fi

[ -e $DIRNAME ] && rm -rf $DIRNAME
mkdir -p $DIRNAME
chmod 777 $DIRNAME

touch $LOCK_FILE || (echo "Can't create lock file $LOCK_FILE. Exiting..." && exit 0)

# Saves file descriptors for later being restored
exec 3>&1 4>&2
trap 'exec 2>&4 1>&3' 0 1 2 3
# Redirect stdout and stderr to a log file
exec 1>$LOG 2>&1

# Set and trap a function to be called in always when the scripts exits in error
function onEXIT {
  # Delete lock file
  [ -e $LOCK_FILE ] && rm -fr $LOCK_FILE

  # Save workdir and clean
#  cd $DIRNAME && mkdir -p _previous_bmk_results_$(whoami)
#  tar -czf bmk_out_`date +"%d%m%Y_%s"`.tar.gz $DIRNAME 2>/dev/null
#    rm -fr $RUNAREA_PATH $DIRTMP $PARSER_PATH && mv bmk_out*.tar.gz $PREVIOUS_RESULTS_DIR
#  fi

  if [ $END -eq 0 ]; then
    echo -e "\n
!! ERROR !!: \nThe script encountered a problem. Exiting without finishing.
Log snippet ($LOG):
***************************\n" >&3
    tail -15 $LOG >&3
    echo -e "\n***************************" >&3
  else
    echo "INFO: Finished benchmark"
    echo -e "\nExiting...\n" >&3
  fi
}
trap onEXIT EXIT

# Get parameters
QUIET=0
CLOUD='test'
FREE_TEXT=''
HS06_PATH=''
HS06_URL=''
HS06_BMK=''
HS06_ITER=3
SPEC2017_PATH=''
SPEC2017_URL=''
SPEC2017_BMK='pure_rate_cpp'
SPEC2017_ITER=3
while [ "$1" != "" ]; do
  case $1 in
    -q    )                 QUIET=1;
    ;;
    -o    )                 OFFLINE=1;
    ;;
    --benchmarks=*  )       BENCHMARKS=${1#*=};
    ;;
    --mp_num=*  )           MP_NUM=${1#*=};
    ;;
    --uid=*    )            VMUID=${1#*=};
    ;;
    --public_ip=* )         PUBLIC_IP=${1#*=};
    ;;
    --cloud=* )             CLOUD=${1#*=};
    ;;
    --vo=* )                VO=${1#*=};
    ;;
    --pnode=* )             PNODE=${1#*=};
    ;;
    --queue_port=* )        QUEUE_PORT=${1#*=};
    ;;
    --queue_host=* )        QUEUE_HOST=${1#*=};
    ;;
    --username=* )          QUEUE_USERNAME=${1#*=};
    ;;
    --password=* )          QUEUE_PASSWORD=${1#*=};
    ;;
    --amq_key=* )           AMQ_KEY=${1#*=};
    ;;
    --amq_cert=* )          AMQ_CERT=${1#*=};
    ;;
    --topic=* )             QUEUE_NAME=${1#*=};
    ;;
    --freetext=* )          FREE_TEXT=${1#*=};
    ;;
    --hs06_path=* )         HS06_PATH=${1#*=};
    ;;
    --hs06_url=* )          HS06_URL=${1#*=};
    ;;
    --hs06_bmk=* )          HS06_BMK=${1#*=};
    ;;
    --hs06_iter=* )         HS06_ITER=${1#*=};
    ;;
    --spec2017_path=* )     SPEC2017_PATH=${1#*=};
    ;;
    --spec2017_url=* )      SPEC2017_URL=${1#*=};
    ;;
    --spec2017_bmk=* )      SPEC2017_BMK=${1#*=};
    ;;
    --spec2017_iter=* )     SPEC2017_ITER=${1#*=};
    ;;
    -d )  DEBUG=1
    ;;
    -h )        echo -e "${usage}" >&3
    END=1
    exit 0
    ;;
    * )         echo -e "Invalid option $1 \n\n${usage}" >&3
    END=1
    exit 1
  esac
  shift
done


# No point moving forward if bmks are not specified
if [[ -z $BENCHMARKS ]]
then
  echo "No benchmarks provided. Please use --benchmarks. Exiting..." >&3
  echo "WARN: --benchmarks not specified: $BENCHMARKS. Exit"
  exit 1
else
  bmks=$(echo $BENCHMARKS | tr ";" "\n")
fi

# Exit when any command fails. To allow failing commands, add "|| true"
set -o errexit

[ ! -z $DEBUG ] && echo "DEBUG is $DEBUG" && set -x

echo "
  #######################################
  ###    CERN Benchmarking Suite      ###
  #######################################
"

echo "INFO: Log file at $LOG" >&3

NUM_CPUS=`grep -c processor /proc/cpuinfo`


echo "`date`: Starting benchmark..."

if [[ -z $VMUID ]]
then
  if [ -f /proc/sys/kernel/random/boot_id  ]
  then
    VMUID=`hostname -s`_`cat /proc/sys/kernel/random/boot_id`
  else
    VMUID=`hostname -s`_$(date -d  "`who -b | sed -e 's@system boot@@'`" +%s)
  fi
fi

if [[ -z $PUBLIC_IP ]]
then
  if ! hash ifconfig 2>/dev/null
  then
    call_ifconfig=`whereis ifconfig | awk -F' ' '{print $2}'`
  else
    call_ifconfig="ifconfig"
  fi

  if [[ "$($call_ifconfig eth0)" == *"eth0"* ]]
  then
    PUBLIC_IP=`$call_ifconfig eth0 | grep "inet " | awk -F' ' '{print $2}' | awk -F':' '{print $NF}'`
  else
    echo 'WARN: could not find eth0 IP address. IP parameter not defined!'
  fi
fi

if [ $CLOUD == "test" ] && [ $QUIET -eq 0 ]
then
  echo "CLOUD name is set to 'test'" >&3
fi

# Set auxiliary directories and variables
DIRTMP="$DIRNAME/bmk_utils"
TIMES_SOURCE_PATH="$DIRTMP/times.source"
PARSER_PATH="$DIRTMP/parser"
RUNAREA_PATH="$DIRNAME/bmk_run"
RESULTS_FILE="$DIRTMP/result_profile.json"
PREVIOUS_RESULTS_DIR="$DIRNAME/_previous_bmk_results"
UNIX_BENCH="$ROOTDIR/byte-unixbench/UnixBench"

[ -e $DIRTMP ] && rm -rf $DIRTMP
mkdir -p $DIRTMP
chmod 777 $DIRTMP

if [[ ! -z $MP_NUM ]] && [ $MP_NUM -ne $NUM_CPUS ]
then
  export BENCHMARK_TARGET="core"
else
  export BENCHMARK_TARGET="machine"
  MP_NUM=$NUM_CPUS
fi
echo "export BENCHMARK_TARGET=$BENCHMARK_TARGET" > $TIMES_SOURCE_PATH

function write_parser {

  #Parse the tests
  cat <<X5_EOF >$PARSER_PATH
source $TIMES_SOURCE_PATH
export DB12=$DB12
export HWINFO=$HWINFO
export FREE_TEXT="$FREE_TEXT"
export PNODE=$PNODE
export MP_NUM=$MP_NUM
python $wrapper_basedir/parser.py -i $VMUID -c $CLOUD -v $VO -f $RESULTS_FILE -p $PUBLIC_IP -d $RUNAREA_PATH
X5_EOF

  chmod ugo+rx $PARSER_PATH
}

function run_report(){
    export HWINFO=$(get_classification)

    echo "export end_tests=`date +%s`" >> $TIMES_SOURCE_PATH

    wrapper_basedir=$ROOTDIR/pyscripts
    write_parser

    $PARSER_PATH 

    if [ -z $OFFLINE ]
    then
	set +x
	python $wrapper_basedir/send_queue.py --port=$QUEUE_PORT --server=$QUEUE_HOST \
	    --username=$QUEUE_USERNAME --password=$QUEUE_PASSWORD --name=$QUEUE_NAME \
	    --key_file=$AMQ_KEY --cert_file=$AMQ_CERT --file=$RESULTS_FILE
    fi
    
    cd $ROOTDIR/pyscripts
    python -c "import parser; parser.print_results_from_file(\"$RESULTS_FILE\")" >&3
    cd -


    
}

function get_classification {
  # replaces hwinfo.rb
  vendor_id=`lscpu | grep "Vendor ID" | awk -F' ' '{print $NF}'`
  if [[ $vendor_id == "GenuineIntel" ]]
  then
    vendor="i"
  elif [[ $vendor_id == "AuthenticAMD" ]]
  then
    vendor="a"
  else
    vendor="o"
  fi

  osmajorrelease=$(cat /etc/redhat-release | cut -d "." -f 1 | awk '{print $NF}')

  cpus=${NUM_CPUS:-$(grep -c processor /proc/cpuinfo)}
  cpufamily=`lscpu | grep "CPU family" | awk -F' ' '{print $NF}'`
  cpumodel=`lscpu | grep "Model:" | awk -F' ' '{print $NF}'`
  cpu_stepping=`lscpu | grep Stepping | awk -F' ' '{print $NF}'`
  cpu_speed=`lscpu | grep MHz | awk -F' ' '{print $NF}'`

  echo ${vendor}${osmajorrelease}_${cpus}_f${cpufamily}m${cpumodel}s${cpu_stepping}_mhz${cpu_speed}
}


function run_DB12 {
  # Expects all the variables below to be set
  # Also has optional $1 as basedir for the results
  DB12_RUNAREA=${1:-$RUNAREA_PATH"/DB12"}

  [ -e $DB12_RUNAREA ] && rm -rf $DB12_RUNAREA
  mkdir -p $DB12_RUNAREA

  cp -f "$ROOTDIR/pyscripts/DB12.py" $DB12_RUNAREA

  python $DB12_RUNAREA/DB12.py --cpu_num=$MP_NUM
}

function run_kv {
  # Receives the following arguments:
  #   - $1 is the TIMES_SOURCE file path
  #   - $2 is the current path, where the package is

  TIMES_SOURCE=$1   #FIXME: is still needed?
  ROOTDIR=$2        #FIXME: is still needed?
  RUNAREA=$RUNAREA_PATH/KV

  DOCKER_IMAGE_KV=gitlab-registry.cern.ch/hep-benchmarks/hep-workloads/atlas-kv-bmk:ci1.1

  echo "export init_kv_test=`date +%s`" >> $TIMES_SOURCE
  KVCOPIES=${MP_NUM:-$(grep -c processor /proc/cpuinfo)}

  [ -e $RUNAREA ] && rm -rf $RUNAREA
  mkdir -p $RUNAREA

  cd $RUNAREA

  REFDATE=`date +\%y-\%m-\%d_\%H-\%M-\%S`
  KVLOG=$RUNAREA/kv_$REFDATE.out

  echo "Running KV by: docker run --rm -v $RUNAREA:/results  $DOCKER_IMAGE_KV -c $KVCOPIES -W > $KVLOG"
  docker run --rm -v $RUNAREA:/results  $DOCKER_IMAGE_KV -c $KVCOPIES -W  -- > $KVLOG
  echo "export end_kv_test=`date +%s`" >> $TIMES_SOURCE

  cd $ROOTDIR
}


function run_hepscore {
  # Receives the following arguments:

  RUNAREA=$RUNAREA_PATH/HEPSCORE
  [ -e $RUNAREA ] && rm -rf $RUNAREA
  mkdir -p $RUNAREA

  REFDATE=`date +\%y-\%m-\%d_\%H-\%M-\%S`
  HEPSCORELOG=$RUNAREA/hepscore_$REFDATE.stdout

  echo "Running   hep-score -d -v -f $ROOTDIR/scripts/hepscore/hepscore.yaml -o $RUNAREA/hepscore_result.json $RUNAREA -- > $HEPSCORELOG"
  hep-score -d -v -f $ROOTDIR/scripts/hepscore/hepscore.yaml -o $RUNAREA/hepscore_result.json $RUNAREA -- > $HEPSCORELOG
}

function download_tarball(){
    INSTALL_PATH=$1
    TAR_URL=$2
    [[ ! -e ${INSTALL_PATH}/tmp_download ]] && mkdir -p ${INSTALL_PATH}/tmp_download 
    wget -nv ${TAR_URL} -O ${INSTALL_PATH}/tmp_download/tar_file 
    if [[ $? -ne 0 ]];
    then 
	echo "ERROR downloading package from ${TAR_URL}"
	rm -rf ${URL_PATH}/tmp_download 
	return 1
    fi
    #ln -s /hs06/SPEC_CPU2006_v1.2.tar.bz2 hs06_file #FIXME tmp
    cd ${INSTALL_PATH}
    tar -xaf ${INSTALL_PATH}/tmp_download/tar_file
    rm -rf ${INSTALL_PATH}/tmp_download # in order to reduce space occupancy
}

function prepare_spec(){
#function to check the SPEC configuration (downlaod path, running path) 
#and in case untar the application
 
SPECNAME=$1 
SPECEXE=$2
SPECPATH=$3
SPECURL=$4


    [[ ! -e ${RUNAREA_PATH}/${SPECNAME} ]] && mkdir -p ${RUNAREA_PATH}/${SPECNAME}

    #This path is mandatory. The SPEC2017 installation is expected to be here or to be downlaoded here
    if [[ -z ${SPECPATH} ]];
    then
	echo "ERROR: Unable to find directory for ${SPECNAME}. Please define it using --${SPECNAME,,}_path=your_path_to_it. Exit from run_${SPECNAME,,} without running" >&4
	return 1
    fi

    # if user requests to download from a url then
    # download the file in $SPECUR and untar it, to be then in $SPECPATH
    # NB: if the dir $SPECPATH already exists, the untar will add files
    if [[ ! -z ${SPECURL} ]];
    then
	download_tarball ${SPECPATH} ${SPECURL}
	if [[ $? -ne 0 ]];
	then 
	    echo "Exit from ${SPECNAME}">&4  
	    return 1
	fi	
    fi

    #find the SPEC dir, it could be in a subdir
    cd ${SPECPATH}/
    echo "loogking for ${SPECEXE}"
    CHECKPATH=$(find . -path "*${SPECEXE}")
    if [[ -z ${CHECKPATH} ]];
	then
	echo "ERROR: unable to find ${SPECEXE} in the path ${SPECPATH}. Exit from run_${SPECNAME,,} without running" >&4
	return 1
    fi
    cd $(dirname "$CHECKPATH")/.. #bin/runspec
}

function run_hs06() {
    HS06_ARCH=${1#hs06_}

    prepare_spec "HS06" "bin/runspec" "$HS06_PATH" "$HS06_URL" 
    if [[ $? -ne 0 ]];
    then 
	return 1
    fi	

    HS06_INSTALLATION_PATH=$(pwd)

    cp $ROOTDIR/scripts/spec2k6/linux*-gcc_cern.cfg ${HS06_INSTALLATION_PATH}/config 
    [[ $? -ne 0 ]] && echo "Failing to copy config file $ROOTDIR/scripts/spec2k6/linux*-gcc_cern.cfg to ${HS06_INSTALLATION_PATH}/config" && return 1

    mkdir -p ${RUNAREA_PATH}/HS06
    . $ROOTDIR/scripts/spec2k6/runhs06.sh 
    echo "...${HS06_ARCH}..."
    if [[ -z $HS06_BMK ]];
    then
	runhs06 -a ${HS06_ARCH} -f ${RUNAREA_PATH}/HS06 -s ${HS06_INSTALLATION_PATH} -n ${MP_NUM} -i ${HS06_ITER}
    else
	runhs06 -a ${HS06_ARCH} -f ${RUNAREA_PATH}/HS06 -s ${HS06_INSTALLATION_PATH} -n ${MP_NUM} -i ${HS06_ITER} -b ${HS06_BMK}
    fi
}

function run_spec2017() {
# prepare environment and run script for SPEC2017
    prepare_spec "SPEC2017" "bin/runcpu" "$SPEC2017_PATH" "$SPEC2017_URL" 

    if [[ $? -ne 0 ]];
    then 
	return 1
    fi	
    SPEC2017_INSTALLATION_PATH=$(pwd)

    cp $ROOTDIR/scripts/spec2017/cern*.cfg ${SPEC2017_INSTALLATION_PATH}/config && cp $ROOTDIR/scripts/spec2017/pure_rate_cpp.bset ${SPEC2017_INSTALLATION_PATH}/benchspec/CPU/
    [[ $? -ne 0 ]] && echo "Failing to copy config file $ROOTDIR/scripts/spec2017/cern*.cfg or $ROOTDIR/scripts/spec2017/pure_rate_cpp.bset to ${SPEC2017_INSTALLATION_PATH}/config" && return 1

    mkdir -p "${RUNAREA_PATH}/SPEC2017"
    . "$ROOTDIR/scripts/spec2017/runspec2017.sh" 
    runspec2017 -f "${RUNAREA_PATH}/SPEC2017" -s "${SPEC2017_INSTALLATION_PATH}" -n "${MP_NUM}" -i "${SPEC2017_ITER}" -b "${SPEC2017_BMK}"

}