from influxdb import InfluxDBClient
import pandas as pd
import os
import concurrent.futures

# InfluxDB connection settings
host = 'localhost'  # Update with your InfluxDB host
port = 8086  # Update with your InfluxDB port
database = 'TcpExperiments'  # InfluxDB database name

# Create an InfluxDB client
client = InfluxDBClient(host, port)
client.switch_database(database)

def import_csv_to_influxdb(csv_file, measurement_name, start_time, fields):
    try:
        print(f"Importing {csv_file} into measurement {measurement_name}")
        # Read CSV file into a DataFrame, skipping rows with missing data
        df = pd.read_csv(csv_file, sep=',', decimal='.', na_values=[''])

        if df.empty:
            print(f"No data found in {csv_file}")
            return

        print(f"CSV file {csv_file} read successfully. DataFrame shape: {df.shape}")

        # Drop rows with NaN values in the relevant columns
        df.dropna(subset=['flow_id'] + fields, inplace=True)

        unique_flow_ids = df['flow_id'].unique()  # Extract all unique flow_ids
        print(f"Unique flow IDs found: {unique_flow_ids}")

        points = []

        for flow in unique_flow_ids:
            Time = start_time  # Reset Time to start_time for each flow_id
            flow_df = df[df['flow_id'] == flow]  # Filter rows by the current flow_id

            for _, row in flow_df.iterrows():
                try:
                    flow_id = int(row['flow_id'])  # Cast flow_id to int

                    # Determine the correct Time_sec field based on the file type
                    if 'interval_sec' in row:
                        Time_sec = float(row['interval_sec'])
                    elif 'Time_sec' in row:
                        Time_sec = float(row['Time_sec'])
                    elif 'time_stamp' in row:
                        Time_sec = float(row['time_stamp'])
                    else:
                        Time_sec = float(row['time_stamp_sec'])
                        
                    if pd.isna(Time_sec):
                        # print(f"Skipping row with NaN Time_sec: {row}")
                        continue

                    Time = start_time + pd.Timedelta(seconds=Time_sec)  # Add Time_sec to timeframe

                    fields_data = {"Time_sec": Time_sec}
                    for field in fields:
                        fields_data[field] = float(row[field])

                    # If casting was successful, add the data to points
                    point = {
                        "measurement": measurement_name,
                        "tags": {"flow_id": flow_id},
                        "time": Time,
                        "fields": fields_data
                    }
                    points.append(point)
                except (ValueError, TypeError) as e:
                    # Handle the case where casting to the expected data types fails
                    print(f"Skipping row with invalid data: {row} - Error: {e}")

        if points:
            # Write data to InfluxDB in smaller batches
            batch_size = 5000
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                success = client.write_points(batch)
                if success:
                    print(f"Batch {i//batch_size + 1} written successfully.")
                else:
                    print(f"Batch {i//batch_size + 1} failed to write.")
            print(f"Data imported from {csv_file} to InfluxDB.")
        else:
            print(f"No valid points to write from {csv_file}")
    except Exception as e:
        print(f"Error importing data from {csv_file}: {str(e)}")

def process_directory_structure(aqm_config, cca_config, speed_config, bdp_config, base_path):
    tasks = []
    for aqm in aqm_config:
        has_ecn = aqm != "fifo"
        for cca_combo in cca_config:
            for speed in speed_config:
                for bdp in bdp_config:
                    for run in range(1, 2):
                        row = {
                            "cca1": cca_combo['cca1'],
                            "cca2": cca_combo['cca2'],
                            "speed": speed['tag'], 
                            "aqm": aqm,
                            "bdp": bdp,
                            "run": run
                        }

                        s1 = f"{base_path}/poseidon-sender-1_output/output/{speed['tag']}_{cca_combo['cca1']}_{cca_combo['cca2']}_{aqm}_{bdp}bdp_{run}"
                        s2 = f"{base_path}/poseidon-sender-2_output/output/{speed['tag']}_{cca_combo['cca2']}_{cca_combo['cca1']}_{aqm}_{bdp}bdp_{run}"
                        r1 = f"{base_path}/poseidon-router-1_output/output/{speed['tag']}_{cca_combo['cca1']}_{cca_combo['cca2']}_{aqm}_{bdp}bdp_{run}_buffer"
                            
                        # Select appropriate buffer file based on AQM
                        if aqm == "fq_codel":
                            buffer_file_r1 = f"{r1}/buffer_status_fq_codel.csv"
                        elif aqm == "red":
                            buffer_file_r1 = f"{r1}/buffer_status_red.csv"
                        else:
                            buffer_file_r1 = f"{r1}/buffer_status.csv"


                        file_name_s1 = f"sender_1_{speed['tag']}_{cca_combo['cca1']}_{cca_combo['cca2']}_{aqm}_{bdp}bdp_{run}"
                        file_name_s2 = f"sender_2_{speed['tag']}_{cca_combo['cca2']}_{cca_combo['cca1']}_{aqm}_{bdp}bdp_{run}"

                        # Load the DataFrame from the CSV file, specifying that the first row is the header
                        df = pd.read_csv(f'{s1}/ping_active_rtt.csv', header=0)
                        first_timestamp = df['original_time_stamp'].iloc[0]
                        start_time = pd.to_datetime(first_timestamp, unit='s')
                        # print(f"Start time for {s1}: {start_time}")

                        tasks.append((f'{s1}/{file_name_s1}_buffer_dropped.csv', f'{file_name_s1}_buffer_dropped', start_time, ['dropped_pkts']))
                        tasks.append((f'{s1}/{file_name_s1}_buffer_overlimit.csv', f'{file_name_s1}_buffer_overlimit', start_time, ['overlimits_pkts']))
                        tasks.append((f'{s1}/{file_name_s1}_iperf_cwnd.csv', f'{file_name_s1}_iperf_cwnd', start_time, ['Cwnd_MBytes']))
                        tasks.append((f'{s1}/{file_name_s1}_rtt.csv', f'{file_name_s1}_rtt', start_time, ['rtt_ms']))
                        tasks.append((f'{s1}/{file_name_s1}_probe_rtt.csv', f'{file_name_s1}_probe_rtt', start_time, ['rtt_ms']))
                        tasks.append((f'{s1}/{file_name_s1}_retx.csv', f'{file_name_s1}_retx', start_time, ['retx_sum_pkts']))
                        tasks.append((f'{s1}/{file_name_s1}_iperf_retx.csv', f'{file_name_s1}_iperf_retx', start_time, ['Retx_pkts']))
                        if has_ecn:
                            tasks.append((f'{s1}/{file_name_s1}_ecn.csv', f'{file_name_s1}_ecn', start_time, ['ECE_FLAG', 'CWR_FLAG']))
                        
                        tasks.append((f'{s2}/{file_name_s2}_iperf_cwnd.csv', f'{file_name_s2}_iperf_cwnd', start_time, ['Cwnd_MBytes']))
                        tasks.append((f'{s2}/{file_name_s2}_rtt.csv', f'{file_name_s2}_rtt', start_time, ['rtt_ms']))
                        tasks.append((f'{s2}/{file_name_s2}_probe_rtt.csv', f'{file_name_s2}_probe_rtt', start_time, ['rtt_ms']))
                        tasks.append((f'{s2}/{file_name_s2}_retx.csv', f'{file_name_s2}_retx', start_time, ['retx_sum_pkts']))
                        tasks.append((f'{s2}/{file_name_s2}_iperf_retx.csv', f'{file_name_s2}_iperf_retx', start_time, ['Retx_pkts']))
                        if has_ecn:
                            tasks.append((f'{s2}/{file_name_s2}_ecn.csv', f'{file_name_s2}_ecn', start_time, ['ECE_FLAG', 'CWR_FLAG']))
    
                        with concurrent.futures.ThreadPoolExecutor(max_workers=14) as executor:
                            futures = [executor.submit(import_csv_to_influxdb, *task) for task in tasks]
                            for future in concurrent.futures.as_completed(futures):
                                try:
                                    future.result()
                                except Exception as exc:
                                    print(f'Task generated an exception: {exc}')

# Main script
speed_config = [
    {"tag": "1gbps", "speed": 1000000000, "processes": 10, "parallel_streams": 1},
    {"tag": "10gbps", "speed": 10000000000, "processes": 20, "parallel_streams": 5},
    {"tag": "25gbps", "speed": 25000000000, "processes": 25, "parallel_streams": 10},
    {"tag": "40gbps", "speed": 40000000000, "processes": 25, "parallel_streams": 10}
]

cca_config = [
    # {"cca1": "bbr1", "cca2": "cubic"},
    {"cca1": "bbr2", "cca2": "cubic"},
    {"cca1": "bbr3", "cca2": "cubic"},
    {"cca1": "htcp", "cca2": "cubic"},
    {"cca1": "cubic", "cca2": "cubic"},
    {"cca1": "bbr1", "cca2": "bbr1"},
    {"cca1": "bbr2", "cca2": "bbr2"},
    {"cca1": "bbr3", "cca2": "bbr3"},
    {"cca1": "htcp", "cca2": "htcp"}
]

aqm_config = ["fifo", "fq_codel", "red"]

bdp_config = [1, 2, 4]

base_path = "/data2/imtiaz/bbrv3_new/final_data"

process_directory_structure(aqm_config, cca_config, speed_config, bdp_config, base_path)

# Close the InfluxDB client connection
client.close()