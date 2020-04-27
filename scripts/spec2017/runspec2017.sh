#!/bin/bash

#set -x 

function usage () {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Where OPTIONS can be:"
    echo " -h"
    echo "    Display this help and exit"
    echo " -f path"
    echo "    Directory where the results will be dumped. By default, it is"
    echo "    $RESULTDIR."
    echo " -r"
    echo "    Run a rate metric, instead of the default speed metric."
    echo " -b benchmark"
    echo "    Benchmark to run: pure_rate_cpp. The default is $BENCHMARK."
    echo " -s specdir"
    echo "    Directory where the benchmark is installed. The default is $SPECDIR."
    echo " -c configfile"
    echo "    Use customized config file. This default is $CONFIG."
    echo " -n number_of_copies"
    echo "    Number of benchmark copies to be started at the same time in rate or"
    echo "    parallel runs. The default is $COUNT."
    echo " -i"
    echo "    number of iterations (default=3)"
    echo
}

function fail () {
    echo $1 >&2
    #exit -1
}

function compute_spec2017_results() {

    SPECDIR=$1
    # Calculate the result
    # First, lets get a list of the runs to look for (001, 002, etc.)
    RUNS=""
    for n in $SPECDIR/result/CPU2017.*.log;
    do
	RUNS="$RUNS `echo $n | sed 's/^.*CPU2017\.\(\w\+\)\.log/\1/'`"
    done
    echo "RUNS $RUNS"

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
    [[ $TOTRUNS -gt 0 ]] && AVERAGE=`echo "scale=3; ($SUM)/$TOTRUNS" | bc | awk '{printf "%.3f", $0 }'`
    SUM=`echo "scale=2; ($SUM)/1" | bc | awk '{printf "%.3f", $0 }'`
    echo "Final result: $SUM  over $TOTRUNS runs. Average $AVERAGE"

    #The file result/CPU2017.001.log is the first generated doing build
    SWCOMPILER=`grep -ir sw_compiler $SPECDIR/result/CPU2017.001.log | sort | uniq | cut -d"=" -f2 | tr "\n" " "`
    OPTIMIZE=`grep "^OPTIMIZE" $SPECDIR/result/CPU2017.001.log  | sort | uniq | cut -d"=" -f2`
    EXTRA_COPTIMIZE=`grep "^EXTRA_COPTIMIZE" $SPECDIR/result/CPU2017.001.log  | sort | uniq | cut -d"=" -f2`
    BSET=`grep "action=build" $SPECDIR/result/CPU2017.001.log | awk -F 'action=build' '{print $2}' | sed -e 's@ @@g'`
    RUNCPU_ARGS=`grep -i  "runcpu command" $SPECDIR/result/CPU2017.00*csv | sort | uniq  | grep config  | awk -F '"runcpu command:",' '{print $2}' | sort | uniq -c | tr "\n" ";" | sed -e 's@"@@g' -e 's@\s\{2,10\}@@g'`

    #Now build the JSON output that will be used for the suite
    JSON="{\"spec2017\":{\"start\":\"$START\", \"end\":\"$END\", 
             \"compiler\":\"$SWCOMPILER\", \"optimize\":\"$OPTIMIZE\", 
              \"extra_coptimize\":\"$EXTRA_COPTIMIZE\", \"runcpu_args\":\"$RUNCPU_ARGS\", \"bset\":\"$BSET\",
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


function runspec2017() {
    SPECDIR="/spec2017"
    RESULTDIR="."
    BENCHMARK="pure_rate_cpp"
    COUNT=`grep -c "^processor" /proc/cpuinfo`;
    CONFIG='cern-gcc-linux-x86.cfg'
    ITERATIONS=3

    local OPTIND
    while getopts "hf:a:rb:s:c:n:i:" flag;
    do
	case $flag in
            f ) RESULTDIR=$OPTARG;;
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

    NAME="spec2017-`hostname -s`-`date +%Y%m%d-%H%M%S`"
    START=`date`


    cd $SPECDIR || fail "Unable to find SPEC2017 directory (should be $SPECDIR)"
    SPECDIR=`pwd` #get the absolute path

    if [[ ! -e VERIFIED_INSTALLATION ]];
    then
	./install.sh -f && touch VERIFIED_INSTALLATION || fail "SPEC2017 install failed!" 
    else
	echo "INFO: SPEC2017 installation already verified. Skipping it. If you want to run it in any case remove the file "`pwd`"/VERIFIED_INSTALLATION"
    fi

    # Set up the environment, clean all previous binaries and results, 
    # and then compile the binaries
    . shrc
    runcpu --config=${CONFIG} --action=scrub $BENCHMARK || fail "Error during SPEC2017 cleanup!"
    rm -f result/*  #this is needed to enable the proper parsing of the generated files
    runcpu --config=${CONFIG} --action=build $BENCHMARK || fail "Error during SPEC2017 compile!"


    # Now we're ready to go. 
    #NB: using the rate or the speed depends on the benchamrk that is passed
    for i in `seq $COUNT`;
    do
        runcpu --config=${CONFIG} --nobuild --noreportable --iterations=$ITERATIONS $BENCHMARK > /dev/null || fail "Error during SPEC2017 speed execution!" &
    done

    wait



    # All done! Time to collect results and send them off
    END=`date`

    compute_spec2017_results $SPECDIR
    
    # Prepare "results package"
    cd $RESULTDIR

    echo $JSON > $RESULTDIR/spec2017_result.json

    mkdir $NAME

    cp $SPECDIR/result/*.{txt,log} $NAME/ || fail "Unable to copy results"
    cp $SPECDIR/config/${CONFIG} $NAME/ || fail "Unable to copy configuration file"

    # Tar the whole lot
    tar czf "$NAME.tar.gz" "$NAME/"

    
}


