import subprocess
import csv
import time
import sys
import os

def get_buffer_status(interface, output_directory, min_timestamp):
    cmd = f"tc -s qdisc show dev {interface}"
    output = subprocess.check_output(cmd, shell=True, universal_newlines=True)

    # Parse the output to extract the buffer status
    lines = output.split('\n')
    buffer_status_tbf = {}
    buffer_status_fq_codel = {}
    processing = 0
    for line in lines:
        if "qdisc tbf" in line:
            processing = 1
            continue
        elif "qdisc fq_codel" in line:
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
                    buffer_status_fq_codel['sent_pkts'] = int(tokens[3])
                    dropped_index = tokens.index('(dropped')
                    dropped_value = tokens[dropped_index + 1]
                    dropped_value = dropped_value.replace(',', '')  # Remove the comma
                    buffer_status_fq_codel['dropped_pkts'] = int(dropped_value)
                    overlimits_index = tokens.index('overlimits')
                    buffer_status_fq_codel['overlimits_pkts'] = int(tokens[overlimits_index + 1])
                elif tokens[0] == "backlog":
                    buffer_status_fq_codel['backlog_pkts'] = int(tokens[4])  # Update the index to 4
                    requeues_index = tokens.index('requeues')
                    requeues_value = tokens[requeues_index + 1]
                    requeues_value = requeues_value.rstrip(')')
                    buffer_status_fq_codel['requeues_pkts'] = int(requeues_value)
            else:
                continue

    save_buffer_status_to_csv(buffer_status_tbf, output_directory, min_timestamp, 'buffer_status_tbf.csv')
    save_buffer_status_to_csv(buffer_status_fq_codel, output_directory, min_timestamp, 'buffer_status_fq_codel.csv')

def save_buffer_status_to_csv(buffer_status, output_directory, min_timestamp, filename):
    if buffer_status:
        original_timestamp = time.time()
        timestamp = "{:.3f}".format(original_timestamp - min_timestamp)

        with open(os.path.join(output_directory, filename), 'a', newline='') as csvfile:
            fieldnames = ['original_timestamp', 'time_stamp_sec', 'sent_pkts', 'dropped_pkts', 'overlimits_pkts', 'backlog_pkts', 'requeues_pkts']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Check if the file is empty and write the header if needed
            if os.stat(os.path.join(output_directory, filename)).st_size == 0:
                writer.writeheader()

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
        while time.time() < end_time:
            get_buffer_status(interface, output_directory, min_timestamp)
            time.sleep(0.001)  # Sleep for 1 millisecond
