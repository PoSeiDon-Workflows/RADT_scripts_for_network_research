import sys
import os
import pandas as pd
import re

def extract_port(line):
    match = re.search(r'\[\s*(\d+)\]', line)
    if match:
        return match.group(1)
    return None

def extract_src_dst_ports(line):
    match = re.search(r'local .* port (\d+) connected to .* port (\d+)', line)
    if match:
        src_port = match.group(1)
        dst_port = match.group(2)
        return src_port, dst_port
    return None, None

def convert_cwnd_to_mbytes(cwnd_str):
    cwnd_str = cwnd_str.strip()
    units = {
        'GBytes': 1024 * 1024,
        'MBytes': 1,
        'KBytes': 1 / 1024,
        'Bytes': 1 / (1024 * 1024)
    }
    cwnd_parts = cwnd_str.split()
    cwnd_unit = cwnd_parts[-1]
    if cwnd_unit not in units:
        raise ValueError(f"Unknown cwnd unit: {cwnd_unit}")
    cwnd_value = float(cwnd_parts[-2])
    cwnd = cwnd_value * units[cwnd_unit]
    return round(cwnd, 2)

def convert_throughput_to_mbps(throughput_str):
    throughput_str = throughput_str.strip()
    units = {
        'Gbits/sec': 1000,
        'Mbits/sec': 1,
        'Kbits/sec': 1 / 1000,
        'bits/sec': 1 / (1000 * 1000)
    }
    throughput_parts = throughput_str.split()
    throughput_unit = throughput_parts[-1]
    if throughput_unit not in units:
        raise ValueError(f"Unknown throughput unit: {throughput_unit}")
    throughput_value = float(throughput_parts[-2])
    throughput = throughput_value * units[throughput_unit]
    return round(throughput, 2)

def extract_time_and_data(line):
    columns = line.split()
    if len(columns) < 9:
        raise ValueError(f"Invalid line format: {line.strip()}")
    time_str = columns[2]
    time_start, time_end = map(float, time_str.split('-'))
    time = time_end
    throughput_str = columns[6] + " " + columns[7]
    retx = columns[8]
    cwnd_value_str = columns[9]
    cwnd_unit = columns[10]

    return time, throughput_str, retx, cwnd_value_str, cwnd_unit

# Initialize an empty DataFrame
df = pd.DataFrame()
# Initialize an empty list to store DataFrame chunks
df_chunks = []

# Get the directory path from the command line argument
if len(sys.argv) != 2:
    print("Usage: python script_name.py directory_path")
    sys.exit(1)

directory = sys.argv[1]
if not os.path.isdir(directory):
    print(f"Error: {directory} is not a valid directory.")
    sys.exit(1)

file_list = [file for file in os.listdir(directory) if file.startswith("iperf_") and file.endswith(".out")]

for filename in file_list:
    # Clear data for the next iteration
    port_data = []
    port_mapping = {}
    
    with open(os.path.join(directory, filename), 'r') as f:
        for line in f:
            if '[' in line and ']' in line:
                port_number = extract_port(line)
                if port_number and port_number not in port_mapping:
                    src_port, dst_port = extract_src_dst_ports(line)
                    if src_port and dst_port:
                        port_mapping[port_number] = {'src_port': src_port, 'dst_port': dst_port}
                    continue

                if port_number in port_mapping and '[ ID]' not in line and '[SUM]' not in line:
                    try:
                        time, throughput_str, retx, cwnd_value_str, cwnd_unit = extract_time_and_data(line)
                        cwnd_str = f"{cwnd_value_str} {cwnd_unit}"
                        cwnd = convert_cwnd_to_mbytes(cwnd_str)
                        throughput_mbps = convert_throughput_to_mbps(throughput_str)

                        if retx is not None and cwnd_value_str is not None:
                            src_port = port_mapping[port_number]['src_port']
                            dst_port = port_mapping[port_number]['dst_port']
                            # Create a DataFrame chunk for the current data
                            df_chunk = pd.DataFrame({'src_port': [src_port], 'dst_port': [dst_port], 'Time_sec': [float(time)], 'Retx_pkts': [float(retx)], 'Cwnd_MBytes': [float(cwnd)], 'Throughput_Mbps': [throughput_mbps]})
                            df_chunks.append(df_chunk)
                        else:
                            print(f"If statement: Error processing line: {line.strip()}. Skipping.")
                    except (IndexError, ValueError) as e:
                        print(f"Error processing line: {line.strip()}. Skipping. Error: {e}")

# Concatenate all DataFrame chunks into a single DataFrame
if df_chunks:
    df = pd.concat(df_chunks, ignore_index=True)
    print("DataFrame head after concatenation:")
    print(df.head())

    # Save the entire DataFrame to a single CSV
    df.to_csv(os.path.join(directory, 'iperf_data.csv'), index=False)
    print("Saved the detailed data to iperf_data.csv")

    # Calculate the total time
    total_time_sec = df['Time_sec'].max()
    print(f"Total time (sec): {total_time_sec}")
    if total_time_sec == 0:
        print("Debug: Total time is zero. Skipping throughput calculation.")
    else:
        # Calculate average throughput and total retransmissions per port
        totals_per_port = df.groupby('src_port').agg(
            average_throughput_mbps=('Throughput_Mbps', 'mean'),
            total_retransmissions=('Retx_pkts', 'sum')
        ).reset_index()
        print("Totals per port head:")
        print(totals_per_port.head())

        # Calculate total average throughput and retransmissions per sender
        total_average_throughput_mbps = totals_per_port['average_throughput_mbps'].sum()
        total_throughput_gbps = total_average_throughput_mbps / 1000
        total_retransmissions = totals_per_port['total_retransmissions'].sum()

        # Save the totals per port to a CSV file
        totals_per_port.to_csv(os.path.join(directory, 'iperf_totals_per_port.csv'), index=False, columns=['src_port', 'average_throughput_mbps', 'total_retransmissions'])
        print("Saved the totals per port data to iperf_totals_per_port.csv")

        # Save the totals per sender to a CSV file
        with open(os.path.join(directory, 'iperf_totals_per_sender.csv'), 'w') as f:
            f.write("average_throughput_gbps,total_retransmissions\n")
            f.write(f"{total_throughput_gbps},{total_retransmissions}\n")
        print("Saved the totals per sender data to iperf_totals_per_sender.csv")

else:
    print("No valid data to process.")

print("Script execution completed.")