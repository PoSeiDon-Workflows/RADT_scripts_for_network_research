# RADT Scripts for Network Research

This repository provides a set of scripts and tools for conducting network research, including performance analysis, buffer status inspection, and RTT probing. It is designed to streamline network data collection and post-processing, primarily leveraging `iperf` and other network utilities. The primary goal of the RADT dataset is to provide researchers with detailed insights into the interactions between TCP Congestion Control Algorithms (CCAs) and Active Queue Management (AQM) algorithms under different network conditions, enabling the development of more advanced, AI-driven CCAs.

## Why This Research Was Conducted

The Internet is evolving with increasingly complex traffic patterns, larger data transfers, and the integration of AI/ML-based applications. Existing TCP CCAs struggle to meet the demands of high-bandwidth, low-latency networks. The need for new, more adaptive CCAs is driven by the quest for improved network performance—minimizing latency, ensuring fairness, and optimizing resource utilization across diverse traffic environments.

By analyzing the behavior of various state-of-the-art TCP CCAs (such as BBRv1, BBRv2, BBRv3, HTCP, and CUBIC) and AQM algorithms (FIFO, RED, and FQ-CoDel) under real-world conditions using the FABRIC testbed, we aim to provide valuable insights that are crucial for developing the next generation of self-driving and self-healing networks. This dataset captures interactions between TCP flows, bottleneck routers, and buffer statuses, making it a foundational resource for future AI/ML-based congestion control systems.

## Repository Structure

### `FABRIC_scripts/`
This directory contains scripts to set up network experiments, manage RTT probing, and handle buffer status monitoring. These scripts are designed to be used in the FABRIC testbed environment or similar experimental network infrastructures.

- **`active_rtt_probing.py`**: Script for active round-trip time (RTT) probing across network paths.
- **`bbr3_setup.sh`** & **`bbrv2_setup.sh`**: Shell scripts to set up the BBRv3 and BBRv2 congestion control algorithms, respectively.
- **`buffer_status_fifo.py`**, **`buffer_status_fq_codel.py`**, **`buffer_status_red.py`**: Scripts for monitoring buffer status with FIFO, FQ-CoDel, and RED (Random Early Detection) queuing disciplines.
- **`fabric-setup.ipynb`**: Jupyter notebook providing a setup guide for configuring the FABRIC testbed environment.
- **`process_pcap.py`**: Script for processing pcap (packet capture) files, extracting relevant information for analysis.
- **`start_iperf_client.sh`** & **`start_iperf_server.sh`**: Shell scripts to initiate `iperf` tests for measuring bandwidth between client and server.

### `post_processing/`
This directory includes scripts for processing and analyzing the data collected during experiments.

- **`count_ecn.py`**: Counts the number of ECN (Explicit Congestion Notification) marks in network traffic.
- **`gather_total.sh`**: Shell script to aggregate the results of experiments across different runs.
- **`influxdb_database.py`**: Script for sending data to an InfluxDB database for storage and further analysis.
- **`parser.py`**: Parses experimental results from various output formats for further analysis.
- **`plot_all.py`**: Script to generate comprehensive visualizations of all collected data.
- **`plot_summary_from_csv.py`**: Creates summary plots from CSV files.
- **`plot_totals.sh`**: Shell script for plotting total results from aggregated data.
- **`process_iperf.py`**: Processes the results from `iperf` tests to generate insights and statistics.
- **`save_csv_for_summary.py`**: Saves processed results in CSV format for further analysis or visualization.

## Requirements

To run the scripts in this repository, you will need:

- Python 3.x
- Jupyter Notebook (optional, for `fabric-setup.ipynb`)
- InfluxDB (optional, for data storage)
- Shell scripting support (bash)
- `iperf` (for bandwidth measurement, we used iperf3 modified by ESNet)

## Usage

### Network Setup and Data Collection

1. **Set up FABRIC environment** (optional for FABRIC users):
   - Follow the instructions in the `fabric-setup.ipynb` notebook to configure the environment.

2. **Run experiments**:
   - Set up congestion control using the provided BBR scripts:
     - For BBRv1, BBRv3, HTCP, Reno, CUBIC:
       ```bash
       ./bbr3_setup.sh
       ```
      - For BBRv2:
         ```bash
         ./bbrv2_setup.sh
         ```

   - Start `iperf` tests by running the client and server scripts on respective machines:
     ```bash
     ./start_iperf_server.sh
     ./start_iperf_client.sh
     ```

3. **Monitor Buffer Status**:
   - Use buffer status scripts depending on the queuing discipline:
     ```bash
     python buffer_status_fifo.py
     ```

4. **Active RTT Probing**:
   - To actively probe the network RTT, run:
     ```bash
     python active_rtt_probing.py
     ```

### Post-Processing Data

After running your experiments, use the post-processing scripts to analyze the results:

1. **Count ECN Marks**:
   ```bash
   python count_ecn.py --input <input_pcap_file>

2. **Aggregate Results**:
   ```bash
   ./gather_total.sh

3. **Store in InfluxDB (optional)**:
   ```bash
   python influxdb_database.py --data <data_file>

4. **Generate Plots**:
   - **To plot all collected data**:
     ```bash
     python plot_all.py --input <input_csv_file>
     ```
   - **For summary plots**:
     ```bash
     python plot_summary_from_csv.py --input <input_csv_file>
     ```

5. **Process iperf Results**:
   ```bash
   python process_iperf.py --input <iperf_output_file>

## Contributions and Future Work

The RADT dataset is intended to serve as a foundation for future research into TCP congestion control, particularly the development of AI/ML-based CCAs. We encourage contributions to this repository and the dataset to further advance network performance optimization.


## Support

If you encounter any issues or have questions, please open an issue in the repository. Or you can contact: Imtiaz Mahmud (imtiaz.tee@gmail.com, imahmud@lbl.gov)
