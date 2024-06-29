#!/usr/bin/env bash
bw=$1
cca1=$2
cca2=$3
aqm=$4
bdp=$5
run=$6
upper_limit_port=$(($7 + 10))
mkdir -p output/${bw}_${cca1}_${cca2}_${aqm}_${bdp}_${run}
for i in $(seq 11 1 $upper_limit_port); do 
        $(iperf3 -s -p 156${i} -f m > output/${bw}_${cca1}_${cca2}_${aqm}_${bdp}_${run}/iperf_${i}.out 2>&1 &);
done
