import subprocess
import time
import csv
import argparse
import os


def ping_and_record(src_ip, dst_ip, run_time, interval, output_directory):
    start_time = time.time()
    end_time = start_time + run_time
    file_path = f"{output_directory}/ping_active_rtt.csv"

    with open(file_path, mode="w", newline="") as csv_file:
        fieldnames = ["original_time_stamp", "time_stamp", "src_ip", "dst_ip", "rtt_ms"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        while time.time() < end_time:
            original_time_stamp = time.time()

            # First ping to warm up the connection
            subprocess.run(
                ["ping", "-c", "1", "-W", "1", dst_ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Second ping to measure RTT
            response = subprocess.run(
                ["ping", "-c", "1", "-W", "1", dst_ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            #print("Ping output:", response.stdout)
            #print("Ping error:", response.stderr)

            if response.returncode == 0:
                time_stamp = "{:.3f}".format(original_time_stamp - start_time)
                output_lines = response.stdout.split('\n')
                for line in output_lines:
                    if "time=" in line:
                        rtt_str = line.split("time=")[1].split()[0]
                        rtt = float(rtt_str)
                        writer.writerow(
                            {
                                "original_time_stamp": original_time_stamp,
                                "time_stamp": time_stamp,
                                "src_ip": src_ip,
                                "dst_ip": dst_ip,
                                "rtt_ms": rtt,
                            }
                        )

            time.sleep(interval / 1000)  # Convert interval to seconds

    print(f"Ping and recording completed for {run_time} seconds.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ping and record RTT")
    parser.add_argument("src_ip", type=str, help="Source IP address")
    parser.add_argument("dst_ip", type=str, help="Destination IP address")
    parser.add_argument("run_time", type=int, help="Run time in seconds")
    parser.add_argument("interval", type=int, help="Interval in milliseconds")
    parser.add_argument("bw", type=str, help="Bandwidth")
    parser.add_argument("cca1", type=str, help="CCA1")
    parser.add_argument("cca2", type=str, help="CCA2")
    parser.add_argument("aqm", type=str, help="AQM")
    parser.add_argument("bdp", type=str, help="BDP")
    parser.add_argument("run", type=str, help="Run identifier")
    args = parser.parse_args()

    output_directory = f"output/{args.bw}_{args.cca1}_{args.cca2}_{args.aqm}_{args.bdp}_{args.run}"
    os.makedirs(output_directory, exist_ok=True)

    ping_and_record(
        args.src_ip, args.dst_ip, args.run_time, args.interval, output_directory
    )
