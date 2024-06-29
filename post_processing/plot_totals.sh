#!/usr/bin/env bash

#./gather_totals.sh
#python3 parser.py

for i in $(find . -name *.dat); do
for j in {1..10}; do
  sed -i 's/,0\.0,/,0\.0001,/g' $i
done
done

cwd=$(pwd)
aqms=("fifo" "fq_codel" "red")
bws=("1gbps" "10gbps" "25gbps" "40gbps")

for j in parsed_data/*; do
if [[ -d $j ]]; then

i=${j#*/}

echo "$i - ${i%_*} - ${i#*_}"
alg1=${i%_*}
alg2=${i#*_}

cd ${cwd}/${j}
    
for aqm in ${aqms[@]}; do

filename="throughput_retx_${alg1}_${alg2}_${aqm}_boxes.pdf"
csv_filename="throughput_retx_${alg1}_${alg2}_${aqm}_boxes.csv"
echo $filename

# Save data to CSV
echo "BDP Configuration,alg1_mean_throughput,alg2_mean_throughput,alg1_mean_retx_packets,alg2_mean_retx_packets" > $csv_filename
for bw in ${bws[@]}; do
  cat "${alg1}_${alg2}_${aqm}_${bw}.dat" >> $csv_filename
done

gnuplot<<EOC
    reset
    set terminal pdf size 10,12 font "Calibri, 26"
    set output "$filename"
    set datafile separator ","

    set multiplot layout 2,1 columns
    set style data histogram
    set style fill solid 1 border -1
    set style histogram clustered gap 2
    set boxwidth 0.9
    
    #set title "${alg1} vs ${alg2} - ${aqm}" noenhanced
    set notitle
    
    set ylabel "Throughput Mbps (log)"
    set logscale y
    #set xlabel "BDP Configuration"
    unset xlabel
    set key above vertical maxrows 4 right font "Calibri, 22"
    

    plot "${alg1}_${alg2}_${aqm}_1gbps.dat" using 2:xtic(1) title "1Gbps(10 ${alg1})" ls 1,\
         "${alg1}_${alg2}_${aqm}_1gbps.dat" using 3:xtic(1) title "1Gbps(10 ${alg2})" fillstyle pattern 1 ls 1,\
         "${alg1}_${alg2}_${aqm}_10gbps.dat" using 2:xtic(1) title "10Gbps(100 ${alg1})" ls 2,\
         "${alg1}_${alg2}_${aqm}_10gbps.dat" using 3:xtic(1) title "10Gbps(100 ${alg2})" fillstyle pattern 1 ls 2,\
         "${alg1}_${alg2}_${aqm}_25gbps.dat" using 2:xtic(1) title "25Gbps(250 ${alg1})" ls 3,\
         "${alg1}_${alg2}_${aqm}_25gbps.dat" using 3:xtic(1) title "25Gbps(250 ${alg2})" fillstyle pattern 1 ls 3,\
         "${alg1}_${alg2}_${aqm}_40gbps.dat" using 2:xtic(1) title "40Gbps(250 ${alg1})" ls 4,\
         "${alg1}_${alg2}_${aqm}_40gbps.dat" using 3:xtic(1) title "40Gbps(250 ${alg2})" fillstyle pattern 1 ls 4

    
    set ylabel "reTX Packets (log)"
    set logscale y
    set xlabel "BDP Configuration"
    unset key
    
    plot "${alg1}_${alg2}_${aqm}_1gbps.dat" using 4:xtic(1) title "1Gbps(10 ${alg1})" ls 1,\
         "${alg1}_${alg2}_${aqm}_1gbps.dat" using 5:xtic(1) title "1Gbps(10 ${alg2})" fillstyle pattern 1 ls 1,\
         "${alg1}_${alg2}_${aqm}_10gbps.dat" using 4:xtic(1) title "10Gbps(100 ${alg1})" ls 2,\
         "${alg1}_${alg2}_${aqm}_10gbps.dat" using 5:xtic(1) title "10Gbps(100 ${alg2})" fillstyle pattern 1 ls 2,\
         "${alg1}_${alg2}_${aqm}_25gbps.dat" using 4:xtic(1) title "25Gbps(250 ${alg1})" ls 3,\
         "${alg1}_${alg2}_${aqm}_25gbps.dat" using 5:xtic(1) title "25Gbps(250 ${alg2})" fillstyle pattern 1 ls 3,\
         "${alg1}_${alg2}_${aqm}_40gbps.dat" using 4:xtic(1) title "40Gbps(250 ${alg1})" ls 4,\
         "${alg1}_${alg2}_${aqm}_40gbps.dat" using 5:xtic(1) title "40Gbps(250 ${alg2})" fillstyle pattern 1 ls 4
EOC


filename="fairness_${alg1}_${alg2}_${aqm}_boxes.pdf"
csv_filename="fairness_${alg1}_${alg2}_${aqm}_boxes.csv"
echo $filename

# Save data to CSV
echo "BDP Configuration,Fairness Index" > $csv_filename
for bw in ${bws[@]}; do
  awk -F, '{print $1 "," $6}' "${alg1}_${alg2}_${aqm}_${bw}.dat" >> $csv_filename
done

gnuplot<<EOC
    reset
    set terminal pdf size 16,10 font "Calibri, 26"
    set output "$filename"
    set datafile separator ","

    set style data histogram
    set style fill solid 1 border -1
    set style histogram clustered gap 2
    set boxwidth 0.9
    
    #set title "Fairness: ${alg1} vs ${alg2} - ${aqm}" noenhanced
    set notitle
    
    set yrange [0:]
    set ylabel "Fairness Index"
    set xlabel "BDP Configuration"
    set key above horizontal right font "Calibri, 22"
    
    plot "${alg1}_${alg2}_${aqm}_1gbps.dat" using 6:xtic(1) title "1Gbps" ls 1,\
         "${alg1}_${alg2}_${aqm}_10gbps.dat" using 6:xtic(1) title "10Gbps" ls 2,\
         "${alg1}_${alg2}_${aqm}_25gbps.dat" using 6:xtic(1) title "25Gbps" ls 3,\
         "${alg1}_${alg2}_${aqm}_40gbps.dat" using 6:xtic(1) title "40Gbps" ls 4
EOC

#########################################################

filename="throughput_retx_${alg1}_${alg2}_${aqm}_lines.pdf"
csv_filename="throughput_retx_${alg1}_${alg2}_${aqm}_lines.csv"
echo $filename

# Save data to CSV
echo "BDP Configuration,alg1_mean_throughput,alg2_mean_throughput,alg1_mean_retx_packets,alg2_mean_retx_packets" > $csv_filename
for bw in ${bws[@]}; do
  cat "${alg1}_${alg2}_${aqm}_${bw}.dat" >> $csv_filename
done

gnuplot<<EOC
    reset
    set terminal pdf size 10,12 font "Calibri, 26"
    set output "$filename"
    set datafile separator ","

    set multiplot layout 2,1 columns
    
    #set title "${alg1} vs ${alg2} - ${aqm}" noenhanced
    set notitle
    
    set ylabel "Throughput Mbps (log)"
    set logscale y
    unset xlabel
    set key above vertical maxrows 4 right font "Calibri, 22"
    
    plot "${alg1}_${alg2}_${aqm}_1gbps.dat" using 2:xtic(1) title "1Gbps(10 ${alg1})" with linespoints lw 5 pt 1,\
         "${alg1}_${alg2}_${aqm}_1gbps.dat" using 3:xtic(1) title "1Gbps(10 ${alg2})" with linespoints lw 5 pt 1,\
         "${alg1}_${alg2}_${aqm}_10gbps.dat" using 2:xtic(1) title "10Gbps(100 ${alg1})" with linespoints lw 5 pt 3,\
         "${alg1}_${alg2}_${aqm}_10gbps.dat" using 3:xtic(1) title "10Gbps(100 ${alg2})" with linespoints lw 5 pt 3,\
         "${alg1}_${alg2}_${aqm}_25gbps.dat" using 2:xtic(1) title "25Gbps(250 ${alg1})" with linespoints lw 5 pt 5,\
         "${alg1}_${alg2}_${aqm}_25gbps.dat" using 3:xtic(1) title "25Gbps(250 ${alg2})" with linespoints lw 5 pt 5,\
         "${alg1}_${alg2}_${aqm}_40gbps.dat" using 2:xtic(1) title "40Gbps(250 ${alg1})" with linespoints lw 5 pt 7,\
         "${alg1}_${alg2}_${aqm}_40gbps.dat" using 3:xtic(1) title "40Gbps(250 ${alg2})" with linespoints lw 5 pt 7

    
    set ylabel "reTX Packets (log)"
    set xlabel "BDP Configuration"
    unset key

    plot "${alg1}_${alg2}_${aqm}_1gbps.dat" using 4:xtic(1) title "1Gbps(10 ${alg1})" with linespoints lw 5 pt 1,\
         "${alg1}_${alg2}_${aqm}_1gbps.dat" using 5:xtic(1) title "1Gbps(10 ${alg2})" with linespoints lw 5 pt 1,\
         "${alg1}_${alg2}_${aqm}_10gbps.dat" using 4:xtic(1) title "10Gbps(100 ${alg1})" with linespoints lw 5 pt 3,\
         "${alg1}_${alg2}_${aqm}_10gbps.dat" using 5:xtic(1) title "10Gbps(100 ${alg2})" with linespoints lw 5 pt 3,\
         "${alg1}_${alg2}_${aqm}_25gbps.dat" using 4:xtic(1) title "25Gbps(250 ${alg1})" with linespoints lw 5 pt 5,\
         "${alg1}_${alg2}_${aqm}_25gbps.dat" using 5:xtic(1) title "25Gbps(250 ${alg2})" with linespoints lw 5 pt 5,\
         "${alg1}_${alg2}_${aqm}_40gbps.dat" using 4:xtic(1) title "40Gbps(250 ${alg1})" with linespoints lw 5 pt 7,\
         "${alg1}_${alg2}_${aqm}_40gbps.dat" using 5:xtic(1) title "40Gbps(250 ${alg2})" with linespoints lw 5 pt 7
EOC

filename="throughput_${alg1}_${alg2}_${aqm}_detailed.pdf"
csv_filename="throughput_${alg1}_${alg2}_${aqm}_detailed.csv"
echo $filename

# Save data to CSV
echo "BDP Configuration,alg1_mean_throughput,alg2_mean_throughput,total_throughput" > $csv_filename
for bw in ${bws[@]}; do
  awk -F, '{print $1 "," $2 "," $3 "," ($2+$3)}' "${alg1}_${alg2}_${aqm}_${bw}.dat" >> $csv_filename
done

gnuplot<<EOC
    reset
    set terminal pdf size 10,12 font "Calibri, 22"
    set output "$filename"
    set datafile separator ","

    set multiplot layout 3,2 columns
    
    set ylabel "Throughput Mbps"
    unset xlabel
    set key top right font "Calibri, 18"
    

    set title "1Gbps (10 vs 10 flows)" noenhanced
    plot "${alg1}_${alg2}_${aqm}_1gbps.dat" using 2:xtic(1) title "${alg1}" with linespoints lw 5,\
         "${alg1}_${alg2}_${aqm}_1gbps.dat" using 3:xtic(1) title "${alg2}" with linespoints lw 5,\
         "${alg1}_${alg2}_${aqm}_1gbps.dat" using (\$2+\$3):xtic(1) title "total" with linespoints lw 5
    
    set title "10Gbps (100 vs 100 flows)" noenhanced
    plot "${alg1}_${alg2}_${aqm}_10gbps.dat" using 2:xtic(1) title "${alg1}" with linespoints lw 5,\
         "${alg1}_${alg2}_${aqm}_10gbps.dat" using 3:xtic(1) title "${alg2}" with linespoints lw 5,\
         "${alg1}_${alg2}_${aqm}_10gbps.dat" using (\$2+\$3):xtic(1) title "total" with linespoints lw 5

    set title "25Gbps (250 vs 250 flows)" noenhanced
    plot "${alg1}_${alg2}_${aqm}_25gbps.dat" using 2:xtic(1) title "${alg1}" with linespoints lw 5,\
         "${alg1}_${alg2}_${aqm}_25gbps.dat" using 3:xtic(1) title "${alg2}" with linespoints lw 5,\
         "${alg1}_${alg2}_${aqm}_25gbps.dat" using (\$2+\$3):xtic(1) title "total" with linespoints lw 5

    set title "40Gbps (250 vs 250 flows)" noenhanced
    plot "${alg1}_${alg2}_${aqm}_40gbps.dat" using 2:xtic(1) title "${alg1}" with linespoints lw 5,\
         "${alg1}_${alg2}_${aqm}_40gbps.dat" using 3:xtic(1) title "${alg2}" with linespoints lw 5,\
         "${alg1}_${alg2}_${aqm}_40gbps.dat" using (\$2+\$3):xtic(1) title "total" with linespoints lw 5
EOC

done

cd ${cwd}

fi
done


#### EXTRA MULTIPLOTS ####

folders_of_interest=("bbr1_bbr1" "bbr2_bbr2" "bbr3_bbr3" "htcp_htcp" "cubic_cubic")
for i in ${folders_of_interest[@]}; do
if [[ -d parsed_data/$i ]]; then

echo "$i - ${i%_*} - ${i#*_}"
alg1=${i%_*}
alg2=${i#*_}

cd ${cwd}/parsed_data/${i}
    
for aqm in ${aqms[@]}; do

echo "#bws,alg1_mean_throughput_1BDP,alg2_mean_throughput_1BDP,alg1_mean_retx_packets_1BDP,alg2_mean_retx_packets_1BDP,fairness_1BDP,alg1_mean_throughput_4BDP,alg2_mean_throughput_4BDP,alg1_mean_retx_packets_4BDP,alg2_mean_retx_packets_4BDP,fairness_4BDP" > "${alg1}_${alg2}_${aqm}_transformed.dat"
for bw in ${bws[@]}; do
  echo "${bw},$(grep '1BDP' ${alg1}_${alg2}_${aqm}_${bw}*.dat | cut -d',' -f 2,3,4,5,6),$(grep '4BDP' ${alg1}_${alg2}_${aqm}_${bw}*.dat | cut -d',' -f 2,3,4,5,6)" >> "${alg1}_${alg2}_${aqm}_transformed.dat"
done

for j in {1..10}; do
  sed -i 's/,0\.0,/,0\.0001,/g' "${alg1}_${alg2}_${aqm}_transformed.dat"
done

done
cd ${cwd}
fi
done

for aqm in ${aqms[@]}; do

filename="parsed_data/throughput_1bdp_4bdp_${aqm}_lines.pdf"
csv_filename="parsed_data/throughput_1bdp_4bdp_${aqm}_lines.csv"
echo $filename

# Save data to CSV
echo "Bandwidth,1BDP_alg1_mean_throughput,1BDP_alg2_mean_throughput,4BDP_alg1_mean_throughput,4BDP_alg2_mean_throughput" > $csv_filename
for i in ${folders_of_interest[@]}; do
  alg1=${i%_*}
  alg2=${i#*_}
  for bw in ${bws[@]}; do
    echo "${bw},$(grep '1BDP' parsed_data/${i}/${alg1}_${alg2}_${aqm}_${bw}*.dat | cut -d',' -f 2,3),$(grep '4BDP' parsed_data/${i}/${alg1}_${alg2}_${aqm}_${bw}*.dat | cut -d',' -f 2,3)" >> $csv_filename
  done
done

gnuplot<<EOC
    reset
    set terminal pdf size 10,12 font "Calibri, 26"
    set output "$filename"
    set datafile separator ","

    set multiplot layout 2,1 columns
    
    set notitle
    
    set ylabel "1BDP - Throughput Mbps"
    unset xlabel
    set key above vertical maxrows 1 right font "Calibri, 22"
    
    plot "parsed_data/bbr1_bbr1/bbr1_bbr1_${aqm}_transformed.dat" using (\$2+\$3):xtic(1) title "BBRv1" with linespoints lw 5 pt 1,\
         "parsed_data/bbr2_bbr2/bbr2_bbr2_${aqm}_transformed.dat" using (\$2+\$3):xtic(1) title "BBRv2" with linespoints lw 5 pt 3,\
         "parsed_data/bbr3_bbr3/bbr3_bbr3_${aqm}_transformed.dat" using (\$2+\$3):xtic(1) title "BBRv3" with linespoints lw 5 pt 5,\
         "parsed_data/htcp_htcp/htcp_htcp_${aqm}_transformed.dat" using (\$2+\$3):xtic(1) title "HTCP" with linespoints lw 5 pt 7,\
         "parsed_data/cubic_cubic/cubic_cubic_${aqm}_transformed.dat" using (\$2+\$3):xtic(1) title "CUBIC" with linespoints lw 5 pt 9

    set ylabel "4BDP - Throughput Mbps"
    set xlabel "Bandwidth"
    unset key
    
    plot "parsed_data/bbr1_bbr1/bbr1_bbr1_${aqm}_transformed.dat" using (\$7+\$8):xtic(1) title "BBRv1" with linespoints lw 5 pt 1,\
         "parsed_data/bbr2_bbr2/bbr2_bbr2_${aqm}_transformed.dat" using (\$7+\$8):xtic(1) title "BBRv2" with linespoints lw 5 pt 3,\
         "parsed_data/bbr3_bbr3/bbr3_bbr3_${aqm}_transformed.dat" using (\$7+\$8):xtic(1) title "BBRv3" with linespoints lw 5 pt 5,\
         "parsed_data/htcp_htcp/htcp_htcp_${aqm}_transformed.dat" using (\$7+\$8):xtic(1) title "HTCP" with linespoints lw 5 pt 7,\
         "parsed_data/cubic_cubic/cubic_cubic_${aqm}_transformed.dat" using (\$7+\$8):xtic(1) title "CUBIC" with linespoints lw 5 pt 9
EOC

filename="parsed_data/retx_1bdp_4bdp_${aqm}_lines.pdf"
csv_filename="parsed_data/retx_1bdp_4bdp_${aqm}_lines.csv"
echo $filename

# Save data to CSV
echo "Bandwidth,1BDP_alg1_mean_retx_packets,1BDP_alg2_mean_retx_packets,4BDP_alg1_mean_retx_packets,4BDP_alg2_mean_retx_packets" > $csv_filename
for i in ${folders_of_interest[@]}; do
  alg1=${i%_*}
  alg2=${i#*_}
  for bw in ${bws[@]}; do
    echo "${bw},$(grep '1BDP' parsed_data/${i}/${alg1}_${alg2}_${aqm}_${bw}*.dat | cut -d',' -f 4,5),$(grep '4BDP' parsed_data/${i}/${alg1}_${alg2}_${aqm}_${bw}*.dat | cut -d',' -f 4,5)" >> $csv_filename
  done
done

gnuplot<<EOC
    reset
    set terminal pdf size 10,12 font "Calibri, 26"
    set output "$filename"
    set datafile separator ","

    set multiplot layout 2,1 columns
    
    set notitle
    
    set ylabel "1BDP - reTX Packets (log)"
    set logscale y
    unset xlabel
    set key above vertical maxrows 1 right font "Calibri, 22"
    
    plot "parsed_data/bbr1_bbr1/bbr1_bbr1_${aqm}_transformed.dat" using (\$4+\$5):xtic(1) title "BBRv1" with linespoints lw 5 pt 1,\
         "parsed_data/bbr2_bbr2/bbr2_bbr2_${aqm}_transformed.dat" using (\$4+\$5):xtic(1) title "BBRv2" with linespoints lw 5 pt 3,\
         "parsed_data/bbr3_bbr3/bbr3_bbr3_${aqm}_transformed.dat" using (\$4+\$5):xtic(1) title "BBRv3" with linespoints lw 5 pt 5,\
         "parsed_data/htcp_htcp/htcp_htcp_${aqm}_transformed.dat" using (\$4+\$5):xtic(1) title "HTCP" with linespoints lw 5 pt 7,\
         "parsed_data/cubic_cubic/cubic_cubic_${aqm}_transformed.dat" using (\$4+\$5):xtic(1) title "CUBIC" with linespoints lw 5 pt 9

    set ylabel "4BDP - reTX Packets (log)"
    set xlabel "Bandwidth"
    unset key
    
    plot "parsed_data/bbr1_bbr1/bbr1_bbr1_${aqm}_transformed.dat" using (\$9+\$10):xtic(1) title "BBRv1" with linespoints lw 5 pt 1,\
         "parsed_data/bbr2_bbr2/bbr2_bbr2_${aqm}_transformed.dat" using (\$9+\$10):xtic(1) title "BBRv2" with linespoints lw 5 pt 3,\
         "parsed_data/bbr3_bbr3/bbr3_bbr3_${aqm}_transformed.dat" using (\$9+\$10):xtic(1) title "BBRv3" with linespoints lw 5 pt 5,\
         "parsed_data/htcp_htcp/htcp_htcp_${aqm}_transformed.dat" using (\$9+\$10):xtic(1) title "HTCP" with linespoints lw 5 pt 7,\
         "parsed_data/cubic_cubic/cubic_cubic_${aqm}_transformed.dat" using (\$9+\$10):xtic(1) title "CUBIC" with linespoints lw 5 pt 9
EOC

filename="parsed_data/fairness_1bdp_4bdp_${aqm}_lines.pdf"
csv_filename="parsed_data/fairness_1bdp_4bdp_${aqm}_lines.csv"
echo $filename

# Save data to CSV
echo "Bandwidth,1BDP_Fairness_Index,4BDP_Fairness_Index" > $csv_filename
for i in ${folders_of_interest[@]}; do
  alg1=${i%_*}
  alg2=${i#*_}
  for bw in ${bws[@]}; do
    echo "${bw},$(grep '1BDP' parsed_data/${i}/${alg1}_${alg2}_${aqm}_${bw}*.dat | cut -d',' -f 6),$(grep '4BDP' parsed_data/${i}/${alg1}_${alg2}_${aqm}_${bw}*.dat | cut -d',' -f 6)" >> $csv_filename
  done
done

gnuplot<<EOC
    reset
    set terminal pdf size 10,12 font "Calibri, 26"
    set output "$filename"
    set datafile separator ","

    set multiplot layout 2,1 columns
    
    set notitle
    
    set ylabel "1BDP - Fairness Index"
    set yrange [0:]
    unset xlabel
    set key above vertical maxrows 1 right font "Calibri, 22"
    
    plot "parsed_data/bbr1_bbr1/bbr1_bbr1_${aqm}_transformed.dat" using 6:xtic(1) title "BBRv1" with linespoints lw 5 pt 1,\
         "parsed_data/bbr2_bbr2/bbr2_bbr2_${aqm}_transformed.dat" using 6:xtic(1) title "BBRv2" with linespoints lw 5 pt 3,\
         "parsed_data/bbr3_bbr3/bbr3_bbr3_${aqm}_transformed.dat" using 6:xtic(1) title "BBRv3" with linespoints lw 5 pt 5,\
         "parsed_data/htcp_htcp/htcp_htcp_${aqm}_transformed.dat" using 6:xtic(1) title "HTCP" with linespoints lw 5 pt 7,\
         "parsed_data/cubic_cubic/cubic_cubic_${aqm}_transformed.dat" using 6:xtic(1) title "CUBIC" with linespoints lw 5 pt 9

    set ylabel "4BDP - Fairness Index"
    set xlabel "Bandwidth"
    unset key
    
    plot "parsed_data/bbr1_bbr1/bbr1_bbr1_${aqm}_transformed.dat" using 11:xtic(1) title "BBRv1" with linespoints lw 5 pt 1,\
         "parsed_data/bbr2_bbr2/bbr2_bbr2_${aqm}_transformed.dat" using 11:xtic(1) title "BBRv2" with linespoints lw 5 pt 3,\
         "parsed_data/bbr3_bbr3/bbr3_bbr3_${aqm}_transformed.dat" using 11:xtic(1) title "BBRv3" with linespoints lw 5 pt 5,\
         "parsed_data/htcp_htcp/htcp_htcp_${aqm}_transformed.dat" using 11:xtic(1) title "HTCP" with linespoints lw 5 pt 7,\
         "parsed_data/cubic_cubic/cubic_cubic_${aqm}_transformed.dat" using 11:xtic(1) title "CUBIC" with linespoints lw 5 pt 9
EOC

done

#clean transformed data
#for i in $(find . -name *transformed.dat); do rm -f $i; done

#clean parsed data
#for i in $(find . -name *.dat); do rm -f $i; done

#clean plots
#for i in $(find . -name *.pdf); do rm -f $i; done
