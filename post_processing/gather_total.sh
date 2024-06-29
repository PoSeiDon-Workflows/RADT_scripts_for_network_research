#!/usr/bin/env bash

set_of_directories=("/data2/imtiaz/bbrv3_new/poseidon-sender-1_output/output" "/data2/imtiaz/bbrv3_new/poseidon-sender-2_output/output")
for i in ${set_of_directories[@]}; do
for dir_item in ${i}/*; do
  if [[ -d $dir_item ]]; then
    cat /dev/null > totals.out
    #echo $dir_item
    for file_item in $dir_item/iperf_*.out; do
      if [[ -f $file_item ]]; then
          #grep sender $file_item | cut -d ']' -f 2 | tail -n 1
          grep sender $file_item | cut -d ']' -f 2 | tail -n 1 >> totals.out
      fi
    done
    #paste -sd+ sums.out | bc
    #awk -F' ' '{sum1+=$5;sum2+=$7} END{printf "#throughput,retransmits\n%.2f,%d\n",sum1,sum2;}' totals.out
    awk -F' ' '{sum1+=$5;sum2+=$7} END{printf "#throughput,retransmits\n%.2f,%d\n",sum1,sum2;}' totals.out > ${dir_item}.total
  fi
done
done