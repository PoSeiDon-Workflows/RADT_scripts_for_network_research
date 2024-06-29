#!/usr/bin/env bash

# ./gather_totals.sh
# python3 parser.py

cwd=$(pwd)
aqms=("fifo" "fq_codel" "red")
bws=("1gbps" "10gbps" "25gbps" "40gbps")

#### EXTRA MULTIPLOTS ####

folders_of_interest=("bbr1_bbr1" "bbr1_cubic" "bbr2_bbr2" "bbr2_cubic" "bbr3_bbr3" "bbr3_cubic" "htcp_htcp" "htcp_cubic" "cubic_cubic")

for aqm in ${aqms[@]}; do
    csv_filename="parsed_data/fairness_varpi_vertheta_${aqm}_lines.csv"

    # Save data to CSV
    echo "CCA1,CCA2,Bandwidth,1BDP_Fairness_Index,2BDP_Fairness_Index,4BDP_Fairness_Index,1BDP_varpi,2BDP_varpi,4BDP_varpi,1BDP_vertheta,2BDP_vertheta,4BDP_vertheta" > $csv_filename
    for i in ${folders_of_interest[@]}; do
        alg1=${i%_*}
        alg2=${i#*_}
        for bw in ${bws[@]}; do
            # Verify the data file exists before processing
            data_file=$(ls parsed_data/${i}/${alg1}_${alg2}_${aqm}_${bw}*.dat 2>/dev/null)
            if [ -n "$data_file" ]; then
                echo "${alg1},${alg2},${bw},"\
                "$(grep '1BDP' $data_file | cut -d',' -f 6),"\
                "$(grep '2BDP' $data_file | cut -d',' -f 6),"\
                "$(grep '4BDP' $data_file | cut -d',' -f 6),"\
                "$(grep '1BDP' $data_file | cut -d',' -f 7),"\
                "$(grep '2BDP' $data_file | cut -d',' -f 7),"\
                "$(grep '4BDP' $data_file | cut -d',' -f 7),"\
                "$(grep '1BDP' $data_file | cut -d',' -f 8),"\
                "$(grep '2BDP' $data_file | cut -d',' -f 8),"\
                "$(grep '4BDP' $data_file | cut -d',' -f 8)" >> $csv_filename
            else
                echo "Data file not found for ${alg1}_${alg2}_${aqm}_${bw}"
            fi
        done
    done
done
