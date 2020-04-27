#!/bin/bash

# Adapted for benchmark suite by Domenico Giordano @ cern.ch
# 2017/09/27
# start from the official runspec.sh script from:
# SPEC2006 Benchmarking Script, Deluxe Edition
# by Alex Iribarren (Alex.Iribarren@cern.ch)

usage () {
    echo "SPEC2006 Benchmarking Script, Deluxe Edition"
    echo "by Alex Iribarren (Alex.Iribarren@cern.ch)"
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Where OPTIONS can be:"
    echo " -h"
    echo "    Display this help and exit"
    echo " -f /afs/cern.ch/..."
    echo "    Directory where the results will be dumped. By default, it is"
    echo "    $RESULTDIR."
    echo " -a arch"
    echo "    Architecture to compile for: 32 or 64 (bits). The default is $ARCH."
    echo " -r"
    echo "    Run a rate metric, instead of the default speed metric."
    echo " -b benchmark"
    echo "    Benchmark to run: int, fp or all_cpp. The default is $BENCHMARK."
    echo " -s specdir"
    echo "    Directory where the benchmark is installed. The default is $SPECDIR."
    echo " -c configfile"
    echo "    Use customized config file. This overrides the -a option."
    echo " -n number_of_copies"
    echo "    Number of benchmark copies to be started at the same time in rate or"
    echo "    parallel runs. The default is $COUNT."
    echo " -p"
    echo "    Reuse existing SPEC installation (in ${SPECDIR}/) and don't clean up."
    echo " -i"
    echo "    number of iterations (default=3)"
    echo
}

fail () {
    echo $1 >&2
    #exit -1
}

function calculate_results() {

    SPECDIR=$1
    # Calculate the result
    # First, lets get a list of the runs to look for (001, 002, etc.)
    RUNS=""
    for n in $SPECDIR/result/CPU2006.*.log;
    do
	RUNS="$RUNS `echo $n | sed 's/^.*CPU2006\.\(\w\+\)\.log/\1/'`"
    done

    SUM=0
    TOTRUNS=0
    LISTBMKS=""
    mincount=1000
    maxcount=0
    for n in $RUNS;
    do
	partial=0
	count=0
	# This scary-looking sed expression looks in the results files of a single run
	# (both CINT and CFP files) for the stuff between a line containing all =====,
	# and " Est. SPEC". This is the final results table and lists all the partial results.
	# Within that section, look for lines that look like:
	#   410.bwaves      13590       2690       5.05 *
	# and grab the last number, 5.05
	for b in `sed -n -e '/^=\+$/,/^ Est. SPEC/!d; s/[0-9]\{3\}\.\w\+\s\+[0-9]\+\s\+[0-9]\+\s\+\([0-9.]\+\)\s\+\*/\1/p' $SPECDIR/result/*.$n.*txt 2>/dev/null`;
	do
            partial="$partial + l($b)"
            count=$(($count + 1))
	done
	if [[ $partial != 0 ]]; # "if the above sed read something..."
	then
            # Calculate the geometric average of all the benchmark results for that run (ie. core)
            # The geometric average of three numbers is: (x * y * z)**1/3
            # or, in order to process this with bc: exp( ( ln(x) + ln(y) + ln(z) ) / 3 )
            SUM="$SUM + `echo "scale=8; e(($partial) / $count)" | bc -l`"

	    LISTBMKS="$LISTBMKS `sed -n -e '/^=\+$/,/^ Est. SPEC/!d; s/\([0-9]\{3\}\.\w\+\)\s\+[0-9]\+\s\+[0-9]\+\s\+\([0-9.]\+\)\s\+\*/\1/p' $SPECDIR/result/*.$n.*txt 2>/dev/null`"

	    [[ $count -lt $mincount ]] && mincount=$count
	    [[ $count -gt $maxcount ]] && maxcount=$count
	    TOTRUNS=$(($TOTRUNS+1))
	fi
    done

    [[ $mincount -ne $maxcount ]] && echo "WARNING: potential error. The number of benchmark results is not equal in all runs" && return 1

    # Add up all the geometric averages and round to the second decimal
    AVERAGE=0
    [[ $TOTRUNS -gt 0 ]] && AVERAGE=`echo "scale=2; ($SUM)/$TOTRUNS" | bc`
    SUM=`echo "scale=2; ($SUM)/1" | bc`
    echo "Final result: $SUM  over $TOTRUNS runs. Average $AVERAGE"

    #The file result/CPU2006.001.log is the first generated doing build
    BSET=`grep "action=build" $SPECDIR/result/CPU2006.001.log | awk -F 'action=build' '{print $2}' | sed -e 's@ @@g' | uniq`
    LINK=`grep 'LINK' $SPECDIR/result/CPU2006.001.log | cut -d":" -f2 | uniq -c | tr "\n" ";" | sed -e 's@   @@g'`
    RUNCPU_ARGS=`grep 'runspec:' $SPECDIR/result/CPU2006.*.log | cut -d":" -f2- | uniq  -c | tr "\n" ";" | sed -e 's@   @ @g'`

    #Now build the JSON output that will be used for the suite
    JSON="{\"hs06_$ARCH\":{\"start\":\"$START\", \"end\":\"$END\",
           \"runcpu_args\":\"$RUNCPU_ARGS\", \"bset\":\"$BSET\", \"LINK\":\"$LINK\",
           \"score\":$SUM, \"avg_core_score\" : $AVERAGE, \"num_bmks\":$count ,\"bmks\":{"
    for bmk in `echo $LISTBMKS | tr " " "\n" | sort | uniq`;
    do
	reslist=""
	for res in `sed -n -e "/^=\+$/,/^ Est. SPEC/!d; s/$bmk\s\+[0-9]\+\s\+[0-9]\+\s\+\([0-9.]\+\)\s\+\*/\1/p" $SPECDIR/result/*.[0-9]*.*txt 2>/dev/null`;
	do
	    reslist="$reslist $res," 
	done
	JSON="$JSON \"$bmk\":[ ${reslist%,}],"
    done
    JSON="${JSON%,} }}}"
    
}

function summary_report() {
    # Put together the system description file
    echo -n "SPEC${BENCHMARK}2006 " >> $NAME/system.txt
    if [ $RATE ]; then echo -n "rate " >> $NAME/system.txt; fi
    if [ $ARCH ]; then 
	echo "with ${ARCH}-bit binaries." >> $NAME/system.txt;
    else
	echo "with custom config file $CONFIG." >> $NAME/system.txt;
    fi
    echo "Description:" $DESCRIPTION >> $NAME/system.txt
    echo "Result:" $SUM >> $NAME/system.txt
    for n in $RUNS;
    do
	echo "Values RUN $n " `sed -n -e '/^=\+$/,/^ Est. SPEC/!d; s/[0-9]\{3\}\.\w\+\s\+[0-9]\+\s\+[0-9]\+\s\+\([0-9.]\+\)\s\+\*/\1/p' $NAME/*.$n.*txt 2>/dev/null` >> $NAME/system.txt
	
    done

    echo "Start time:" $START >> $NAME/system.txt
    echo "End time:  " $END >> $NAME/system.txt
    echo >> $NAME/system.txt
    echo "Kernel: `uname -a`" >> $NAME/system.txt
    echo "Processors: `grep -c vendor /proc/cpuinfo` `cat /proc/cpuinfo | grep -m 1 "model name" | cut -d":" -f 2`" >> $NAME/system.txt
    echo "Memory: `grep MemTotal /proc/meminfo | grep -oe '[[:digit:]]\+ kB'`" >> $NAME/system.txt
    echo "GCC: `$USED_CC  --version | head -n1`" >> $NAME/system.txt
    echo "C++: `$USED_CXX --version | head -n1`" >> $NAME/system.txt
    echo "FC:  `$USED_FC  --version | head -n1`" >> $NAME/system.txt
    echo "SPEC2006 version: `cat $SPECDIR/version.txt`" >> $NAME/system.txt
    echo >> $NAME/system.txt
    file $SPECDIR/benchspec/CPU2006/*/exe/*_gcc_cern | cut -d"/" -f 4,6- >> $NAME/system.txt
    echo >> $NAME/system.txt
    cat /proc/cpuinfo >> $NAME/system.txt
    echo >> $NAME/system.txt
    (dmidecode 2>/dev/null || ([ -e dmidecode-output ] && cat dmidecode-output) || echo "No dmidecode output, please run as root, or run this command first: dmidecode > $PWD/dmidecode-output") >> $NAME/system.txt
    echo >> $NAME/system.txt
    (/sbin/lspci || echo "No lspci output, please run as root") >> $NAME/system.txt
}

function runhs06() {
    RESULTDIR="."
    BENCHMARK="all_cpp"
    COUNT=`grep -c "^processor" /proc/cpuinfo`;
    ARCH=''
    CONFIG=''
    ITERATIONS=3

    local OPTIND
    while getopts "hf:a:rb:s:c:n:i:" flag;
    do
	case $flag in
            f ) RESULTDIR=$OPTARG;;
            a ) ARCH=$OPTARG;;
            r ) RATE=1;;
            b ) BENCHMARK=$OPTARG;;
            s ) SPECDIR=$OPTARG;;
            c ) CONFIG=$OPTARG;;
            n ) COUNT=$OPTARG;;
	    i ) ITERATIONS=$OPTARG;;
            h ) usage
		return 1;;
            * ) usage
		return 1;;
	esac
    done

    if [[ $ARCH -ne 32 && $ARCH -ne 64 ]]; then
	fail "Unknown architecture: valid options are '32' and '64'."
    fi
    if [ ! $CONFIG ]; then
	CONFIG="linux${ARCH}-gcc_cern.cfg"
	echo "INFO: HS06 CONFIG file is $CONFIG" 
    else
	ARCH=""
    fi 

    NAME="spec2k6-`hostname -s`-`date +%Y%m%d-%H%M%S`"
    START=`date`


    cd $SPECDIR || fail "Unable to find HS06 directory (should be $SPECDIR)"
    SPECDIR=`pwd` #get the absolute path

    if [[ ! -e VERIFIED_INSTALLATION ]];
    then
	./install.sh -f && touch VERIFIED_INSTALLATION || fail "HS06 install failed!" 
    else
	echo "INFO: HS06 installation already verified. Skipping it. If you want to run it in any case remove the file "`pwd`"/VERIFIED_INSTALLATION"
    fi

    # remember some information from the config file
    USED_CC=`cat  config/${CONFIG}| grep CC| cut -d'=' -f2`
    USED_CXX=`cat config/${CONFIG}| grep CXX| cut -d'=' -f2`
    USED_FC=`cat  config/${CONFIG}| grep FC| cut -d'=' -f2`

    # Set up the environment, clean all previous binaries and results, 
    # and then compile the binaries
    . shrc
    runspec --config=${CONFIG} --action=scrub $BENCHMARK || fail "Error during HS06 cleanup!"
    rm -f result/*
    runspec --config=${CONFIG} --action=build $BENCHMARK || fail "Error during HS06 compile!"


    # Now we're ready to go. 
    if [ $RATE ]; then
	runspec --config=${CONFIG} --nobuild --noreportable --iterations=$ITERATIONS --rate $COUNT $BENCHMARK > /dev/null || fail "Error during HS06 rate execution!" &
    else
	for i in `seq $COUNT`;
	do
            runspec --config=${CONFIG} --nobuild --noreportable --iterations=$ITERATIONS $BENCHMARK > /dev/null || fail "Error during HS06 execution!" &
	done
    fi;
    wait



    # All done! Time to collect results and send them off
    END=`date`
    echo "Benchmark completed:"
    grep "SPEC${BENCHMARK}(R)" result/*.txt

    calculate_results $SPECDIR
    
    # Prepare "results package"
    cd $RESULTDIR

    echo $JSON > $RESULTDIR/hs06_${ARCH}_result.json

    mkdir $NAME

    cp $SPECDIR/result/*.{txt,log} $NAME/ || fail "Unable to copy results"
    cp $SPECDIR/config/${CONFIG} $NAME/ || fail "Unable to copy configuration file"

    #summary_report
    # Tar the whole lot
    tar czf "$NAME.tar.gz" "$NAME/"

    
}


