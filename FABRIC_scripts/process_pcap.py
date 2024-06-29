import sys
from scapy.all import rdpcap, TCP, IP, Raw
import pandas as pd
import os
import subprocess
from decimal import Decimal, ROUND_DOWN
import shutil
from multiprocessing import Pool, cpu_count

def extract_information(pcap_file):
    # Extracts relevant information from pcap file
    packets = rdpcap(pcap_file)
    information = []
    last_time = None
    packet_map = {}  # Create a dictionary to store packets

    for packet_num, packet in enumerate(packets, start=1):
        if packet.haslayer(IP) and packet.haslayer(TCP):
            tcp = packet[TCP]
            # Check for ECN flags: ECE or CWR
            ecn_flag = 1 if ('E' in tcp.flags or 'C' in tcp.flags) else 0  # 'E' for ECE, 'C' for CWR
            ece_flag = 1 if 'E' in tcp.flags else 0  # ECE flag
            cwr_flag = 1 if 'C' in tcp.flags else 0  # CWR flag

            time_stamp = packet.time
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst
            src_port = tcp.sport
            dst_port = tcp.dport
            pkt_num = packet_num
            tcp_seq = tcp.seq
            ack_num = tcp.ack
            tcp_flags = tcp.flags
            payload_indicator = 1 if Raw in packet else 0
            segment_size = len(packet[TCP].payload)
            rwnd = tcp.window

            # Determine congestion window size
            if tcp.flags.P and tcp.flags.A and payload_indicator == 1:
                cwnd = segment_size  # from sender to dest, we are assuming the CWND corresponds to the sent segment size
            else:
                cwnd = None

            packet_map[tcp.seq] = packet
            information.append([time_stamp, time_stamp, src_ip, src_port, dst_ip, dst_port, pkt_num, tcp_flags, payload_indicator,
                                cwnd, rwnd, tcp_seq, ack_num, segment_size, ecn_flag, ece_flag, cwr_flag])

    return information

def process_information_data(information):
    # Processes the extracted information data
    column_names = ['original_time_stamp','time_stamp_sec', 'src_ip', 'src_port', 'dst_ip', 'dst_port', 'pkt_num', 'tcp_flags', 'payload',
                    'cwnd_bytes', 'rwnd_bytes', 'tcp_seq', 'ack_num', 'segment_size_bytes', 'ECN', 'ECE_FLAG', 'CWR_FLAG']
    df = pd.DataFrame(information, columns=column_names)
    df['original_time_stamp'] = pd.to_numeric(df['original_time_stamp'])
    df['time_stamp_sec'] = pd.to_numeric(df['time_stamp_sec'])
    df.sort_values(by=['dst_port', 'src_port', 'time_stamp_sec'], inplace=True)

    # Adjust timestamps relative to the first packet of each destination port
    first_timestamp = df.groupby('dst_port')['time_stamp_sec'].transform('first')
    df['time_stamp_sec'] = (df['time_stamp_sec'] - first_timestamp).round(3)
        
    return df, first_timestamp


def save_to_csv(df, csv_file):
    # Saves the information data to a CSV file
    df.to_csv(csv_file, index=False)



def analyze_retx_from_pcap(pcap_file):
    cmd = ['tshark', '-r', pcap_file, '-Y', 'tcp.analysis.retransmission', '-T', 'fields', '-e',
           'frame.time_epoch', '-e', 'ip.src', '-e', 'tcp.srcport', '-e', 'ip.dst', '-e', 'tcp.dstport', '-e',
           'tcp.analysis.retransmission']

    output = subprocess.check_output(cmd).decode("utf-8").strip().split("\n")
    retx = []

    for line in output: 
        fields = line.split("\t")
        if not fields[0]:
            continue
        time_stamp = float(fields[0])
        src_ip = fields[1] if len(fields) > 1 else 'Unknown'
        src_port = int(fields[2]) if fields[2] else 0
        dst_ip = fields[3] if len(fields) > 3 else 'Unknown'
        dst_port = int(fields[4]) if fields[4] else 0
        retransmitted = int(fields[5]) if fields[5] else 0

        retx.append([time_stamp, time_stamp, src_ip, src_port, dst_ip, dst_port, retransmitted])

    return retx


def process_retx_data(retx, first_timestamp):
    # Processes the extracted retx data
    column_names = ['original_time_stamp','time_stamp_sec', 'src_ip', 'src_port', 'dst_ip', 'dst_port', 'retx_pkts']
    df = pd.DataFrame(retx, columns=column_names)
    df['time_stamp_sec'] = pd.to_numeric(df['time_stamp_sec'])
    df.sort_values(by=['dst_port', 'src_port', 'time_stamp_sec'], inplace=True)

    # Adjust timestamps relative to the first packet of each destination port
    df['time_stamp_sec'] = (df['time_stamp_sec'] - first_timestamp).round(3)
        
    return df


def analyze_rtt_from_pcap(pcap_file):
    # Run tshark command to analyze the pcap file and filter retransmissions
    cmd = ['tshark', '-r', pcap_file, '-Y', 'tcp.analysis.ack_rtt', '-T', 'fields', '-e',
           'frame.time_epoch', '-e', 'ip.src', '-e', 'tcp.srcport', '-e', 'ip.dst', '-e', 'tcp.dstport', '-e',
           'tcp.analysis.ack_rtt']

    output = subprocess.check_output(cmd).decode("utf-8").strip().split("\n")
    rtts = []

    for line in output: 
        fields = line.split("\t")
        if not fields[0]:
            continue
        time_stamp = float(fields[0])
        src_ip = fields[1] if len(fields) > 1 else 'Unknown'
        src_port = int(fields[2]) if fields[2] else 0
        dst_ip = fields[3] if len(fields) > 3 else 'Unknown'
        dst_port = int(fields[4]) if fields[4] else 0
        rtt_ms = round(float(fields[5]) * 1000, 3) if fields[5] is not None else 0

        rtts.append([time_stamp, time_stamp, src_ip, src_port, dst_ip, dst_port, rtt_ms])

    return rtts


def process_rtt_data(rtt, first_timestamp):
    # Processes the extracted rtt data
    column_names = ['original_time_stamp','time_stamp_sec', 'src_ip', 'src_port', 'dst_ip', 'dst_port', 'rtt_ms']
    df = pd.DataFrame(rtt, columns=column_names)
    df['time_stamp_sec'] = pd.to_numeric(df['time_stamp_sec'])
    df.sort_values(by=['dst_port', 'src_port', 'time_stamp_sec'], inplace=True)

    # Adjust timestamps relative to the first packet of each destination port
    df['time_stamp_sec'] = (df['time_stamp_sec'] - first_timestamp).round(3)
        
    return df

def process_pcap_file(pcap_file):
    information = extract_information(pcap_file)
    retx = analyze_retx_from_pcap(pcap_file)
    rtt = analyze_rtt_from_pcap(pcap_file)
    return information, retx, rtt

def main(base_directory):
    pcap_directory = os.path.join(base_directory, 'pcap')
    if os.path.exists(pcap_directory):
        pcap_files = [os.path.join(pcap_directory, file_name) for file_name in os.listdir(pcap_directory)]

        # Use multiprocessing to process pcap files in parallel
        with Pool(processes=(int)(cpu_count()/2)) as pool:
            results = pool.map(process_pcap_file, pcap_files)

        information = []
        retx = []
        rtt = []
        first_timestamp = None

        for info, r, rt in results:
            information.extend(info)
            retx.extend(r)
            rtt.extend(rt)

        info_df, first_timestamp = process_information_data(information)
        retx_df = process_retx_data(retx, first_timestamp)
        rtt_df = process_rtt_data(rtt, first_timestamp)

        information_csv_file = os.path.join(base_directory, 'extracted_information.csv')
        retx_csv_file = os.path.join(base_directory, 'retx.csv')
        rtt_csv_file = os.path.join(base_directory, 'rtt.csv')

        save_to_csv(info_df, information_csv_file)
        save_to_csv(retx_df, retx_csv_file)
        save_to_csv(rtt_df, rtt_csv_file)

        shutil.rmtree(pcap_directory)

        print("Extraction and analysis complete.")

if __name__ == "__main__":
    # Get the base_directory from the command line argument
    if len(sys.argv) > 1:
        base_directory = sys.argv[1]
        print(base_directory)
    else:
        print("Please provide the base_directory as a command-line argument.")
        sys.exit(1)

    main(base_directory)