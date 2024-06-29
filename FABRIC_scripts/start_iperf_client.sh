#!/usr/bin/env bash

bw=$1
cca1=$2
cca2=$3
aqm=$4
bdp=$5
run=$6
upper_limit_port=$(( $7 + 10 ))
client=$8
flows=$9

output_directory="output/${bw}_${cca1}_${cca2}_${aqm}_${bdp}_${run}"
mkdir -p "$output_directory"

pcap_directory_path="${output_directory}/pcap"
mkdir -p "${pcap_directory_path}"
chmod -R 777 "${pcap_directory_path}"

pcap_file="${pcap_directory_path}/capture.pcap"
#tcpdump_command="sudo tcpdump -s 0 -i any -C 100 -W 10000000 -s 0 -w ${pcap_file} > tcp_dump.out 2>&1"
#eval "$tcpdump_command" &
$(sudo tcpdump -s 0 -i any -C 100 -W 10000000 -s 0 -w ${pcap_file} > tcp_dump.out 2>&1 &);

for ((i=11; i<=upper_limit_port; i++)); do
    iperf_output_file="${output_directory}/iperf_${i}.out"
    #iperf_command="iperf3 -c ${client} -p 156${i} -C ${cca1} -t 200 -f m -P ${flows} -M 8900 > ${iperf_output_file} 2>&1"
    $(iperf3 -c ${client} -p 156${i} -C ${cca1} -t 200 -f m -P ${flows} -M 8900 > ${iperf_output_file} 2>&1 &);
    #eval "$iperf_command" &
done


