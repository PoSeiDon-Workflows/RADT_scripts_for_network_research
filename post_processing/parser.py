#!/usr/bin/env python3

import os
import pandas as pd
import numpy as np

def calculate_fairness(throughputs):
    """Calculate the Jain's fairness index for given throughputs."""
    if len(throughputs) == 0 or np.sum(throughputs) == 0:
        return 0
    n = len(throughputs)  # Total number of flows
    sum_of_squares = np.sum(np.square(throughputs))
    square_of_sums = np.square(np.sum(throughputs))
    fairness_index = square_of_sums / (n * sum_of_squares)
    return fairness_index

def calculate_retransmission_ratio(retrans_cca1_vs_cca2, retrans_cubic_vs_cubic):
    """Calculate the relative retransmission value (varpi)."""
    if retrans_cubic_vs_cubic == 0:
        return 0
    return retrans_cca1_vs_cca2 / retrans_cubic_vs_cubic

def calculate_link_utilization(throughputs, total_bandwidth):
    """Calculate the overall link utilization (vartheta)."""
    total_throughput = np.sum(throughputs) * 1000000 #converting the throughput to bps
    return total_throughput / total_bandwidth

def main():
    aqm_config = ["fifo", "fq_codel", "red"]

    speed_config = [
        {"tag": "1gbps", "speed": 1000000000, "processes": 10, "parallel_streams": 1},
        {"tag": "10gbps", "speed": 10000000000, "processes": 20, "parallel_streams": 5},
        {"tag": "25gbps", "speed": 25000000000, "processes": 25, "parallel_streams": 10},
        {"tag": "40gbps", "speed": 40000000000, "processes": 25, "parallel_streams": 10}
    ]

    cca_config = [
        {"cca1": "bbr1", "cca2": "cubic"},
        {"cca1": "bbr2", "cca2": "cubic"},
        {"cca1": "bbr3", "cca2": "cubic"},
        {"cca1": "htcp", "cca2": "cubic"},
        {"cca1": "cubic", "cca2": "cubic"},
        {"cca1": "bbr1", "cca2": "bbr1"},
        {"cca1": "bbr2", "cca2": "bbr2"},
        {"cca1": "bbr3", "cca2": "bbr3"},
        {"cca1": "htcp", "cca2": "htcp"}
    ]

    bdp_config = [1, 2, 4]

    sender_1_output = "poseidon-sender-1_output/output"
    sender_2_output = "poseidon-sender-2_output/output"
    
    rows = []
    for aqm in aqm_config:
        for cca_combo in cca_config:
            for speed in speed_config:
                for bdp in bdp_config:
                    for run in range(1, 2):
                        row = {
                            "aqm": aqm, 
                            "cca1": cca_combo['cca1'],
                            "cca2": cca_combo['cca2'],
                            "speed": speed['tag'], 
                            "bdp": bdp,
                            "run": run
                        }

                        f1 = f"/data2/imtiaz/bbrv3_new/{sender_1_output}/{speed['tag']}_{cca_combo['cca1']}_{cca_combo['cca2']}_{aqm}_{bdp}bdp_{run}/iperf_totals_per_sender.csv"
                        f2 = f"/data2/imtiaz/bbrv3_new/{sender_2_output}/{speed['tag']}_{cca_combo['cca2']}_{cca_combo['cca1']}_{aqm}_{bdp}bdp_{run}/iperf_totals_per_sender.csv"

                        with open(f1, 'r') as f:
                            lines = f.readlines()
                            measurements = list(map(float, lines[1].replace("\n",'').split(",")))
                            row["sender_1_throughput"] = measurements[0]
                            row["sender_1_retransmits"] = measurements[1]

                        with open(f2, 'r') as f:
                            lines = f.readlines()
                            measurements = list(map(float, lines[1].replace("\n",'').split(",")))
                            row["sender_2_throughput"] = measurements[0]
                            row["sender_2_retransmits"] = measurements[1]
                        
                        rows.append(row)

    results = pd.DataFrame.from_dict(rows)

    # Calculate the average retransmissions for cubic vs cubic as the baseline
    cubic_results = results[(results['cca1'] == 'cubic') & (results['cca2'] == 'cubic')]
    avg_retrans_cubic_vs_cubic = cubic_results[['sender_1_retransmits', 'sender_2_retransmits']].mean().mean()

    agg_results = results.drop(columns=["run"]).groupby(by=["aqm", "cca1", "cca2", "speed", "bdp"]).aggregate("mean")
    
    header = ["#BDP", "alg1_mean_throughput", "alg2_mean_throughput", "alg1_mean_retx_packets", "alg2_mean_retx_packets", "fairness_index", "varpi", "vartheta"]
    
    for aqm in aqm_config:
        for cca_combo in cca_config:
            for speed in speed_config:
                output_buffer = [header]
                for bdp in bdp_config:
                    index = (aqm, cca_combo["cca1"], cca_combo["cca2"], speed["tag"], float(bdp))
                    data = agg_results.loc[index]


                    f1 = f"/data2/imtiaz/bbrv3_new/{sender_1_output}/{speed['tag']}_cubic_cubic_{aqm}_{bdp}bdp_{run}/iperf_totals_per_sender.csv"
                    f2 = f"/data2/imtiaz/bbrv3_new/{sender_2_output}/{speed['tag']}_cubic_cubic_{aqm}_{bdp}bdp_{run}/iperf_totals_per_sender.csv"

                    f3 = f"/data2/imtiaz/bbrv3_new/{sender_1_output}/{speed['tag']}_{cca_combo['cca1']}_{cca_combo['cca2']}_{aqm}_{bdp}bdp_{run}/iperf_totals_per_sender.csv"
                    f4 = f"/data2/imtiaz/bbrv3_new/{sender_2_output}/{speed['tag']}_{cca_combo['cca2']}_{cca_combo['cca1']}_{aqm}_{bdp}bdp_{run}/iperf_totals_per_sender.csv"

                    with open(f1, 'r') as f:
                        lines = f.readlines()
                        measurements = list(map(float, lines[1].replace("\n",'').split(",")))
                        cubic_sender_1_retransmits = measurements[1]

                    with open(f2, 'r') as f:
                        lines = f.readlines()
                        measurements = list(map(float, lines[1].replace("\n",'').split(",")))
                        cubic_sender_2_retransmits = measurements[1]

                    with open(f3, 'r') as f:
                        lines = f.readlines()
                        measurements = list(map(float, lines[1].replace("\n",'').split(",")))
                        aqm_sender_1_retransmits = measurements[1]

                    with open(f4, 'r') as f:
                        lines = f.readlines()
                        measurements = list(map(float, lines[1].replace("\n",'').split(",")))
                        aqm_sender_2_retransmits = measurements[1]

                    f5 = f"/data2/imtiaz/bbrv3_new/{sender_1_output}/{speed['tag']}_{cca_combo['cca1']}_{cca_combo['cca2']}_{aqm}_{bdp}bdp_{run}/iperf_totals_per_port.csv"
                    f6 = f"/data2/imtiaz/bbrv3_new/{sender_2_output}/{speed['tag']}_{cca_combo['cca2']}_{cca_combo['cca1']}_{aqm}_{bdp}bdp_{run}/iperf_totals_per_port.csv"
                    df3 = pd.read_csv(f5)
                    df4 = pd.read_csv(f6)

                    # Combining per-port throughputs for fairness calculation
                    throughput_list = np.concatenate((df3['average_throughput_mbps'].values, df4['average_throughput_mbps'].values))
                    fairness_index = calculate_fairness(throughput_list)

                    # Calculate varpi
                    varpi = calculate_retransmission_ratio(aqm_sender_1_retransmits+aqm_sender_2_retransmits, 
                                                           cubic_sender_1_retransmits+cubic_sender_2_retransmits)

                    # Calculate vartheta
                    vartheta = calculate_link_utilization(throughput_list, speed["speed"])

                    output_buffer.append([
                        f"{bdp}BDP",
                        round(data["sender_1_throughput"], 2),
                        round(data["sender_2_throughput"], 2),
                        round(data["sender_1_retransmits"], 2),
                        round(data["sender_2_retransmits"], 2),
                        fairness_index,
                        varpi,
                        vartheta
                    ])

                output_dir = f"/data2/imtiaz/bbrv3_new/parsed_data/{cca_combo['cca1']}_{cca_combo['cca2']}"
                output_file = f"{cca_combo['cca1']}_{cca_combo['cca2']}_{aqm}_{speed['tag']}.dat"
                abs_output_file = os.path.join(output_dir, output_file)
                
                os.makedirs(output_dir, exist_ok=True)

                with open(abs_output_file, "w+") as g:
                    for line in output_buffer:
                        g.write(f"{','.join(map(str,line))}\n")

if __name__ == "__main__":
    main()
