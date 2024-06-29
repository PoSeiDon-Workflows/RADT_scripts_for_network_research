import subprocess
import csv
import time
import sys
import os
import pandas as pd

def get_buffer_status(interface, output_directory, min_timestamp, headers_written=False):
    cmd = f"tc -s qdisc show dev {interface}"
    output = subprocess.check_output(cmd, shell=True, universal_newlines=True)

    # Parse the output to extract the buffer status
    lines = output.split('\n')
    buffer_status_tbf = {}
    buffer_status_red = {}
    processing = 0
    for line in lines:
        if "qdisc tbf" in line:
            processing = 1
            continue
        elif "qdisc red" in line:
            processing = 2
            continue
        elif "Sent" in line or "backlog" in line:
            tokens = line.strip().split()
            if processing == 1:
                if tokens[0] == "Sent":
                    buffer_status_tbf['sent_pkts'] = int(tokens[3])
                    dropped_index = tokens.index('(dropped')
                    dropped_value = tokens[dropped_index + 1]
                    dropped_value = dropped_value.replace(',', '')  # Remove the comma
                    buffer_status_tbf['dropped_pkts'] = int(dropped_value)
                    overlimits_index = tokens.index('overlimits')
                    buffer_status_tbf['overlimits_pkts'] = int(tokens[overlimits_index + 1])
                elif tokens[0] == "backlog":
                    buffer_status_tbf['backlog_pkts'] = int(tokens[4])  # Update the index to 4
                    requeues_index = tokens.index('requeues')
                    requeues_value = tokens[requeues_index + 1]
                    requeues_value = requeues_value.rstrip(')')
                    buffer_status_tbf['requeues_pkts'] = int(requeues_value)
            elif processing == 2:
                if tokens[0] == "Sent":
                    buffer_status_red['sent_pkts'] = int(tokens[3])
                    dropped_index = tokens.index('(dropped')
                    dropped_value = tokens[dropped_index + 1]
                    dropped_value = dropped_value.replace(',', '')  # Remove the comma
                    buffer_status_red['dropped_pkts'] = int(dropped_value)
                    overlimits_index = tokens.index('overlimits')
                    buffer_status_red['overlimits_pkts'] = int(tokens[overlimits_index + 1])
                elif tokens[0] == "backlog":
                    buffer_status_red['backlog_pkts'] = int(tokens[4])  # Update the index to 4
                    requeues_index = tokens.index('requeues')
                    requeues_value = tokens[requeues_index + 1]
                    requeues_value = requeues_value.rstrip(')')
                    buffer_status_red['requeues_pkts'] = int(requeues_value)
            else:
                continue
                
    save_buffer_status_to_csv(buffer_status_tbf, output_directory, min_timestamp, 'buffer_status_tbf.csv', headers_written)
    save_buffer_status_to_csv(buffer_status_red, output_directory, min_timestamp, 'buffer_status_red.csv', headers_written)
    return True  # Indicate that the headers have been written

def save_buffer_status_to_csv(buffer_status, output_directory, min_timestamp, filename, headers_written=False):
    original_timestamp = time.time()
    timestamp = "{:.3f}".format(original_timestamp - min_timestamp)
    
    with open(os.path.join(output_directory, filename), 'a', newline='') as csvfile:
        fieldnames = ['original_timestamp', 'time_stamp_sec', 'sent_pkts', 'dropped_pkts', 'overlimits_pkts', 'backlog_pkts', 'requeues_pkts']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not headers_written:
            writer.writeheader()  # Write headers if not already written
            headers_written = True

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
    if len(sys.argv) < 9:
        print("Please provide the bandwidth, CCA1, CCA2, AQM, BDP, run, interface name, and runtime name as command-line arguments.")
    else:
        bw = sys.argv[1]
        cca1 = sys.argv[2]
        cca2 = sys.argv[3]
        aqm = sys.argv[4]
        bdp = sys.argv[5]
        run = sys.argv[6]
        interface = sys.argv[7]
        runtime = int(sys.argv[8])

        output_directory = f"output/{bw}_{cca1}_{cca2}_{aqm}_{bdp}_{run}_buffer"
        os.makedirs(output_directory, exist_ok=True)

        start_time = time.time()
        end_time = start_time + runtime

        min_timestamp = start_time
        headers_written = False  # Initialize headers_written as False
        while time.time() < end_time:
            headers_written = get_buffer_status(interface, output_directory, min_timestamp, headers_written)
            time.sleep(0.001)  # Sleep for 1 millisecond
