import pandas as pd
import sys

def count_ecn_packets(csv_file):
    try:
        # Load the CSV file into a DataFrame
        df = pd.read_csv(csv_file)

        # Check if 'ECN' column exists
        if 'ECN' in df.columns:
            # Sum the 'ECN' column to count how many packets are flagged
            ecn_count = df['ECN'].sum()
            # Get the total number of packets by counting the number of rows
            total_packets = len(df)
            print(f"Total ECN-flagged packets: {ecn_count}")
            print(f"Total packets: {total_packets}")
        else:
            print("Error: 'ECN' column not found in the CSV file.")
    except FileNotFoundError:
        print(f"Error: File '{csv_file}' not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        count_ecn_packets(csv_file)
    else:
        print("Usage: python count_ecn_packets.py <path_to_csv_file>")
