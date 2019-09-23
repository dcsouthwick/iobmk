#!/bin/bash

# SPEC2006 Benchmarking Script, Deluxe Edition
# by Alex Iribarren (Alex.Iribarren@cern.ch)
# $Revision: 2.23 $ $Date: 2009/08/05 14:20:14 $
#
# Modifications by Manfred Alef (@kit.edu)
# to support SPEC CPU2006 v1.2 benchmark kit
# and to provide new flag to override the number
# of benchmark copies

# Default options
SPECTARBALL="SPEC_CPU2006_v1.2.tar.bz2"
SPECDIR="SPEC_CPU2006_v1.2"

ARCH="32"
EMAIL="Your.Email@Here.com"
RESULTDIR="/afs/cern.ch/project/benchmark/results-spec"
DESCRIPTION=""
BENCHMARK="all_cpp"
CONFIG=""
COUNT=`grep -c "^processor" /proc/cpuinfo`;

usage () {
    echo "SPEC2006 Benchmarking Script, Deluxe Edition"
    echo "by Alex Iribarren (Alex.Iribarren@cern.ch)"
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Where OPTIONS can be:"
    echo " -h"
    echo "    Display this help and exit"
    echo " -e email@cern.ch"
    echo "    Send email containing the results to this address. By default,"
    echo "    the email is sent to $EMAIL."
    echo " -f /afs/cern.ch/..."
    echo "    Directory where the results will be dumped. By default, it is"
    echo "    $RESULTDIR."
    echo " -d description"
    echo "    Description to include in the results file."
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
    echo " -w"
    echo "    Print the calculated score in the appropriate dokuwiki syntax of the"
    echo "    WIKI at hepix.caspur.it/benchmarks so that users can copy-and-paste."
    echo
}

fail () {
    echo $1 >&2
    exit -1
}

while getopts "he:f:d:a:rb:s:c:pw" flag;
do
    case $flag in
        e ) EMAIL=$OPTARG;;
        f ) RESULTDIR=$OPTARG;;
        d ) DESCRIPTION=$OPTARG;;
        a ) ARCH=$OPTARG;;
        r ) RATE=1;;
        b ) BENCHMARK=$OPTARG;;
        s ) SPECDIR=$OPTARG;;
        c ) CONFIG=$OPTARG;;
        n ) COUNT=$OPTARG;;
        p ) PRESERVE=1;;
        w ) WIKI_LINE=1;;
        h ) usage
            exit;;
        * ) usage
            exit 1;;
    esac
done

if [[ $ARCH != "32" && $ARCH != "64" ]]; then
    fail "Unknown architecture: valid options are '32' and '64'."
fi
if [ ! $CONFIG ]; then
    CONFIG="linux${ARCH}-gcc_cern.cfg"
else
    ARCH=""
fi 
if [[ $BENCHMARK != "int" && $BENCHMARK != "fp" && $BENCHMARK != "all_cpp" ]]; then
    fail "Unknown benchmark: valid options are 'int', 'fp' and 'all_cpp'."
fi
NAME="spec2k6-`hostname -s`-`date +%Y%m%d-%H%M%S`"
START=`date`


# Unpack the SPEC tarball and install it, unless its alread there and 
# we were told to reuse it
if [[ ! ($PRESERVE && -e $SPECDIR) ]]; then
    tar xjf $SPECTARBALL || fail "Unable to extract SPECint!"
    cd $SPECDIR || fail "Unable to find SPECint directory (should be $SPECDIR)"
    ./install.sh -f || fail "SPECint install failed!"
    cd ../
fi

cd $SPECDIR || fail "Unable to find SPECint directory (should be $SPECDIR)"
case ${CONFIG} in
  /*|~*)	cp ${CONFIG} config/cern.cfg || fail "Unable to copy configuration file $CONFIG" ;;
  *)		cp ../${CONFIG} config/cern.cfg || fail "Unable to copy configuration file $CONFIG" ;;
esac

# remember some information from the config file
USED_CC=`cat config/cern.cfg| grep CC| cut -d'=' -f2`
USED_CXX=`cat config/cern.cfg| grep CXX| cut -d'=' -f2`
USED_FC=`cat config/cern.cfg| grep FC| cut -d'=' -f2`

# Set up the environment, clean all previous binaries and results, 
# and then compile the binaries
. shrc
runspec --config=cern --action=scrub $BENCHMARK || fail "Error during SPECint cleanup!"
rm -f result/*
runspec --config=cern --action=build $BENCHMARK || fail "Error during SPECint compile!"


# Now we're ready to go. 
if [ $RATE ]; then
    runspec --config=cern --nobuild --noreportable --rate $COUNT $BENCHMARK > /dev/null || fail "Error during SPECint rate execution!" &
else
    for i in `seq $COUNT`;
    do
        runspec --config=cern --nobuild --noreportable $BENCHMARK > /dev/null || fail "Error during SPECint execution!" &
    done
fi;
wait


# All done! Time to collect results and send them off
END=`date`
echo "Benchmark completed:"
grep "SPEC${BENCHMARK}(R)" result/*.txt

# Calculate the result
# First, lets get a list of the runs to look for (001, 002, etc.)
RUNS=""
for n in result/CPU2006.*.log;
do
    RUNS="$RUNS `echo $n | sed 's/^.*CPU2006\.\(\w\+\)\.log/\1/'`"
done

SUM=0
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
    for b in `sed -n -e '/^=\+$/,/^ Est. SPEC/!d; s/[0-9]\{3\}\.\w\+\s\+[0-9]\+\s\+[0-9]\+\s\+\([0-9.]\+\)\s\+\*/\1/p' result/*.$n.*txt 2>/dev/null`;
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
    fi
done
# Add up all the geometric averages and round to the second decimal
SUM=`echo "scale=2; ($SUM)/1" | bc`
echo "Final result: $SUM"

cd ..

# Prepare "results package"
mkdir $NAME
cp $SPECDIR/result/*.{txt,log} $NAME/ || fail "Unable to copy results"
cp $SPECDIR/config/cern.cfg $NAME/ || fail "Unable to copy configuration file"

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

if [ $WIKI_LINE ]; then
  [ -r hepspec-systeminfo.sh ] || fail "Command to create output in WIKI syntax not found"
  ./hepspec-systeminfo.sh $SUM | tee -a $NAME/system.txt
fi

# Tar the whole lot
tar czf "$NAME.tar.gz" "$NAME/"

# Now send an email with the result.
if [[ ! -e "$NAME.tar.gz" ]]; then fail "Error with tar file"; fi
(cat "$NAME/system.txt"; uuencode "$NAME.tar.gz" "$NAME.tar.gz") | mail -s "SPEC2006 results for `hostname` \"$DESCRIPTION\": $SUM" $EMAIL 

# Copy results to AFS
echo "Copying results to $RESULTDIR/$NAME/ ..."
mkdir "$RESULTDIR/$NAME" || fail "Unable to copy results"
cp $NAME/* "$RESULTDIR/$NAME/"

# Clean up
if [ $PRESERVE ]; then
  echo "Keeping  all directories. Finishing."
else
  rm -rf $SPECDIR
  rm -rf $NAME
fi
