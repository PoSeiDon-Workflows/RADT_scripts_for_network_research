import subprocess
import csv
import time
import sys
import os
import pandas as pd

def get_buffer_status(interface, output_file, min_timestamp):
    cmd = f"tc -s qdisc show dev {interface}"
    output = subprocess.check_output(cmd, shell=True, universal_newlines=True)

    # Parse the output to extract the buffer status
    lines = output.split('\n')
    buffer_status = {}
    for line in lines:
        if "Sent" in line or "backlog" in line:
            tokens = line.strip().split()
            if tokens[0] == "Sent":
                buffer_status['sent_pkts'] = int(tokens[3])
                dropped_index = tokens.index('(dropped')
                dropped_value = tokens[dropped_index + 1]
                dropped_value = dropped_value.replace(',', '')  # Remove the comma
                buffer_status['dropped_pkts'] = int(dropped_value)
                overlimits_index = tokens.index('overlimits')
                buffer_status['overlimits_pkts'] = int(tokens[overlimits_index + 1])
            elif tokens[0] == "backlog":
                buffer_status['backlog_pkts'] = int(tokens[4])  # Update the index to 4
                requeues_index = tokens.index('requeues')
                requeues_value = tokens[requeues_index + 1]
                requeues_value = requeues_value.rstrip(')')
                buffer_status['requeues_pkts'] = int(requeues_value)
    
    if buffer_status:
        original_timestamp = time.time()
        timestamp = "{:.3f}".format(original_timestamp - min_timestamp)
    
        with open(output_file, 'a', newline='') as csvfile:
            fieldnames = ['original_timestamp', 'time_stamp_sec', 'sent_pkts', 'dropped_pkts', 'overlimits_pkts', 'backlog_pkts', 'requeues_pkts']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
            writer.writerow({
                'original_timestamp': original_timestamp,
                'time_stamp_sec': timestamp,
                'sent_pkts': buffer_status.get('sent_pkts', 0),
                'dropped_pkts': buffer_status.get('dropped_pkts', 0),
                'overlimits_pkts': buffer_status.get('overlimits_pkts', 0),
                'backlog_pkts': buffer_status.get('backlog_pkts', 0),
                'requeues_pkts': buffer_status.get('requeues_pkts', 0)
            })

if __name__ == '__main__':
    if len(sys.argv) < 8:
        print("Please provide the bandwidth, CCA1, CCA2, AQM, BDP, run, interface name, runtime, and output file name as command-line arguments.")
    else:
        bw = sys.argv[1]
        cca1 = sys.argv[2]
        cca2 = sys.argv[3]
        aqm = sys.argv[4]
        bdp = sys.argv[5]
        run = sys.argv[6]
        interface = sys.argv[7]
        runtime = int(sys.argv[8])
        output_filename = sys.argv[9]

        output_directory = f"output/{bw}_{cca1}_{cca2}_{aqm}_{bdp}_{run}_buffer"
        os.makedirs(output_directory, exist_ok=True)

        start_time = time.time()
        end_time = start_time + runtime
        output_file = os.path.join(output_directory, output_filename)
        
        min_timestamp = start_time

        # Create and write the header to the CSV file
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['original_timestamp', 'time_stamp_sec', 'sent_pkts', 'dropped_pkts', 'overlimits_pkts', 'backlog_pkts', 'requeues_pkts']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

        while time.time() < end_time:
            get_buffer_status(interface, output_file, min_timestamp)
            time.sleep(0.001)  # Sleep for 1 millisecond
