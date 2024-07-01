import sys
import os
import subprocess
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

import cufflinks as cf
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from plotly.offline import iplot, plot

# Function to read and preprocess the data
def read_and_preprocess(file_name):
    print(f"Reading and preprocessing: {file_name}")
    try:
        pd.set_option('display.float_format', lambda x: '%.9f' % x)  # Disable scientific notation
        df = pd.read_csv(file_name, sep=',')
    except Exception as e:
        print(f"Error reading {file_name}: {e}")
        return None, None
    
    # Ensure 'original_time_stamp' is numeric
    df['original_time_stamp'] = pd.to_numeric(df['original_time_stamp'], errors='coerce')
    
    # Debug: print dataframe before sorting
    # print(f"Data before sorting:\n{df.head()}")
    
    # Drop rows with NaN in 'cwnd_bytes'
    df = df.dropna(subset=['cwnd_bytes'])
    
    # Filter rows where 'dst_port' is 15611
    df_dst_port = df[df['dst_port'] == 15611]
    
    # Calculate first timestamp based on the filtered data
    first_timestamp = df_dst_port['original_time_stamp'].min()
    
    # Calculate 'time_stamp_sec' for the entire dataframe using the first timestamp
    df['time_stamp_sec'] = (df['original_time_stamp'] - first_timestamp).round(3)
    
    # Debug: print the first few values of first_timestamp and time_stamp_sec
    # print(f"First timestamp: {first_timestamp}")
    # print(f"Data with calculated time_stamp_sec:\n{df[['dst_port', 'src_port', 'original_time_stamp', 'time_stamp_sec']].head()}")
    
    # Sort values
    df = df.sort_values(by=['dst_port', 'src_port', 'time_stamp_sec'])
    
    # Debug: print dataframe after sorting
    # print(f"Data after sorting:\n{df.head()}")
    
    return df, first_timestamp

# Function to read and preprocess the rtt, retx, and buffer csv files
def process_rtt_and_retx(file_name, first_timestamp):
    # print(f"Processing RTT and RETX: {file_name}")
    try:
        df = pd.read_csv(file_name, sep=',')
    except Exception as e:
        print(f"Error reading {file_name}: {e}")
        return None

    # Ensure 'original_time_stamp' is numeric
    df['original_time_stamp'] = pd.to_numeric(df['original_time_stamp'], errors='coerce')

    df['time_stamp_sec'] = (df['original_time_stamp'] - first_timestamp).round(3)
    
    # Debug: print dataframe after processing
    # print(f"Processed RTT/RETX data:\n{df[['dst_port', 'src_port', 'original_time_stamp', 'time_stamp_sec']].head(10)}")
    
    df = df.sort_values(by=['dst_port', 'src_port', 'time_stamp_sec'])
    return df

# Function to read and preprocess buffer csv files
def process_buffer(file_name, first_timestamp):
    print(f"Processing buffer: {file_name}")
    try:
        df = pd.read_csv(file_name, sep=',')
    except Exception as e:
        print(f"Error reading {file_name}: {e}")
        return None, None

    # Ensure 'original_timestamp' is numeric
    df['original_timestamp'] = pd.to_numeric(df['original_timestamp'], errors='coerce')
    df['dropped_pkts'] = pd.to_numeric(df['dropped_pkts'], errors='coerce')
    df['overlimits_pkts'] = pd.to_numeric(df['overlimits_pkts'], errors='coerce')

    df['time_stamp_sec'] = (df['original_timestamp'] - first_timestamp).round(3)
    
    # Debug: print dataframe after processing
    # print(f"Processed buffer data:\n{df[['original_timestamp', 'time_stamp_sec', 'dropped_pkts', 'overlimits_pkts']].head(10)}")

    buff_dropped = []
    dropped_pkts = 0

    buff_overlimit = []
    overlimit_pkts = 0

    for index, row in df.iterrows(): 
        time = row['time_stamp_sec']
        dropped_pkts_count = row['dropped_pkts'] - dropped_pkts
        dropped_pkts = row['dropped_pkts']
        buff_dropped.append([time, dropped_pkts_count])

        overlimit_pkts_count = row['overlimits_pkts'] - overlimit_pkts
        overlimit_pkts = row['overlimits_pkts']
        buff_overlimit.append([time, overlimit_pkts_count])
    
    dropped_column_names = ['time_stamp_sec', 'dropped_pkts']
    buff_dropped_df = pd.DataFrame(buff_dropped, columns=dropped_column_names)
    
    overlimit_column_names = ['time_stamp_sec', 'overlimits_pkts']    
    buff_overlimit_df = pd.DataFrame(buff_overlimit, columns=overlimit_column_names)
    
    return buff_dropped_df, buff_overlimit_df

# Function to read and preprocess probe rtt csv files
def process_probe_rtt(file_name, first_timestamp):
    print(f"Processing probe RTT: {file_name}")
    try:
        df = pd.read_csv(file_name, sep=',')
    except Exception as e:
        print(f"Error reading {file_name}: {e}")
        return None

    # Ensure 'original_time_stamp' is numeric
    df['original_time_stamp'] = pd.to_numeric(df['original_time_stamp'], errors='coerce')

    df['time_stamp'] = (df['original_time_stamp'] - first_timestamp).round(3)

    return df

# Function to read and preprocess iperf csv files
def process_iperf_data(file_name):
    print(f"Processing iperf data: {file_name}")
    try:
        df = pd.read_csv(file_name, sep=',')
    except Exception as e:
        print(f"Error reading {file_name}: {e}")
        return None, None
    
    df_cwnd = df[['src_port', 'dst_port', 'Time_sec', 'Cwnd_MBytes']]
    df_retx = df[['src_port', 'dst_port', 'Time_sec', 'Retx_pkts']]

    return df_cwnd, df_retx

# Function to plot buffer against time_stamp_sec and save the figure
def plot_buffer_data(df, path):
    fig_name = f'{path}/buffer_status.png'
    
    # Filter DataFrame for rows where 'dropped_pkts' is not equal to 0
    buffer_nonzero = df[df['dropped_pkts'] != 0]
    
    plt.stem(buffer_nonzero['time_stamp_sec'], buffer_nonzero['dropped_pkts'], label='dropped packets',
             linefmt='none', markerfmt='*b', basefmt='y', bottom=0)
    plt.xlim(0, 120)  # Set x-axis limits
    plt.ylim(0, buffer_nonzero['dropped_pkts'].max() + 1)  # Set y-axis limits
    plt.xlabel('time_sec')
    plt.ylabel('dropped_pkts')
    plt.yticks(np.arange(min(buffer_nonzero['dropped_pkts']), max(buffer_nonzero['dropped_pkts'])+1))
    plt.legend()
    plt.savefig(fig_name)  # Save the plot as an image file
    plt.close()  # Close the figure to avoid overlapping plots

# Function to plot cwnd_bytes against time_stamp_sec and save the figure
def plot_cwnd_data(df, dst_port, src_port, path):
    fig_name = f'{path}/cwnd_dst{dst_port}_src{src_port}.png'
    plt.plot(df['time_stamp_sec'], df['cwnd_bytes'], label=f'dst_port={dst_port}, src_port={src_port}')
    plt.xlim(0, 120)  # Set x-axis limits
    plt.ylim(0, df['cwnd_bytes'].max() + 1)  # Set y-axis limits
    plt.xlabel('time_sec')
    plt.ylabel('send_segment_size_bytes')
    plt.legend()
    plt.savefig(fig_name)  # Save the plot as an image file
    plt.close()  # Close the figure to avoid overlapping plots

# Function to plot rtt against time_stamp_sec and save the figure
def plot_rtt_data(df, dst_port, src_port, path):
    fig_name = f'{path}/rtt_dst{src_port}_src{dst_port}.png'
    plt.plot(df['time_stamp_sec'], df['rtt_ms'], label=f'dst_port={src_port}, src_port={dst_port}')
    plt.xlim(0, 120)  # Set x-axis limits
    plt.ylim(0, df['rtt_ms'].max() + 1)  # Set y-axis limits
    plt.xlabel('time_sec')
    plt.ylabel('rtt_msec')
    plt.legend()
    plt.savefig(fig_name)  # Save the plot as an image file
    plt.close()  # Close the figure to avoid overlapping plots

# Function to plot probed rtt against time_stamp_sec and save the figure
def plot_probe_rtt(df, path):
    fig_name = f'{path}/probed_rtt.png'
    plt.plot(df['time_stamp'], df['rtt_ms'], label='probed_rtt')
    plt.xlim(0, 120)  # Set x-axis limits
    plt.ylim(0, df['rtt_ms'].max() + 1)  # Set y-axis limits
    plt.xlabel('time_sec')
    plt.ylabel('probed_rtt_msec')
    plt.legend()
    plt.savefig(fig_name)  # Save the plot as an image file
    plt.close()  # Close the figure to avoid overlapping plots

def plot_retx_data(df, dst_port, src_port, path):
    retx = []
    step = 1
    interval = step
    retx_sum = 0
    retx.append([0, retx_sum])

    for index, row in df.iterrows(): 
        if row['time_stamp_sec'] <= interval:
            retx_sum += row['retx_pkts']
        else:
            retx.append([interval, retx_sum])
            interval += step
            retx_sum = 0
    
    column_names = ['interval_sec','retx_sum_pkts']
    retx_df = pd.DataFrame(retx, columns=column_names)

    fig_name = f'{path}/retx_dst{dst_port}_src{src_port}.png'
    retx_nonzero = retx_df[retx_df['retx_sum_pkts'] != 0]
    plt.stem(retx_nonzero['interval_sec'], retx_nonzero['retx_sum_pkts'], label=f'dst_port={dst_port}, src_port={src_port}')
    plt.xlim(0, 120)  # Set x-axis limits
    plt.ylim(0, retx_nonzero['retx_sum_pkts'].max() + 1)  # Set y-axis limits
    plt.xlabel('time_sec')
    plt.ylabel('retx_pkts')
    plt.legend()
    plt.savefig(fig_name)  # Save the plot as an image file
    plt.close()  # Close the figure to avoid overlapping plots



# Function to plot cwnd_bytes, rtt, ece, and retx in a single figure and save the figure
def plot_combined_data(df_cwnd_list, df_rtt_list, df_retx_list, df_iperf_cwnd_list, 
                       df_iperf_retx_list, df_buffer_dropped, df_buffer_overlimit, df_probe_rtt, df_ecn_list, path, file_name, has_ecn):  
   
    num_plots = 7 if not has_ecn else 8
    fig, axs = plt.subplots(num_plots, 1, sharex=True, figsize=(8, num_plots * 2), constrained_layout=True)
    
    flow_counter = 1  # Initialize the flow counter
    retx_df_list = []

    # Determine max values for y-axes
    y_max_iperf_cwnd = max([df['Cwnd_MBytes'].max() for df in df_iperf_cwnd_list])
    y_max_rtt = max([df['rtt_ms'].max() for df in df_rtt_list])
    y_max_probe_rtt = df_probe_rtt['rtt_ms'].max()
    y_max_retx = max([df['retx_pkts'].max() for df in df_retx_list])
    y_max_iperf_retx = max([df['Retx_pkts'].max() for df in df_iperf_retx_list])
    y_max_buffer_dropped = df_buffer_dropped['dropped_pkts'].max()
    y_max_buffer_overlimit = df_buffer_overlimit['overlimits_pkts'].max()
    if has_ecn:
        y_max_ecn = max([df['ECE_FLAG'].max() for df in df_ecn_list])


# Function to plot cwnd_bytes, rtt, ece, and retx in a single figure and save the figure
def plot_combined_data(df_cwnd_list, df_rtt_list, df_retx_list, df_iperf_cwnd_list, 
                       df_iperf_retx_list, df_buffer_dropped, df_buffer_overlimit, df_probe_rtt, df_ecn_list, path, file_name, has_ecn):  
    num_plots = 7 if not has_ecn else 8
    fig, axs = plt.subplots(num_plots, 1, sharex=True, figsize=(8, num_plots * 1.5), constrained_layout=True)
    
    flow_counter = 1  # Initialize the flow counter
    
    # print(f"df_iperf_cwnd_list head thpt:\n", df_iperf_cwnd_list.head())
    # print(f"df_iperf_cwnd_list head retx:\n", df_iperf_retx_list.head())

    # Determine y-axis limits based on the maximum values across all data
    y_max_iperf_cwnd = max([df['Cwnd_MBytes'].max() for df in df_iperf_cwnd_list]) * 1.1 if df_iperf_cwnd_list else 1
    y_max_rtt = max([df['rtt_ms'].max() for df in df_rtt_list]) * 1.1 if df_rtt_list else 1
    y_max_probe_rtt = df_probe_rtt['rtt_ms'].max() * 1.1 if not df_probe_rtt.empty else 1
    y_max_iperf_retx = max([df['Retx_pkts'].max() for df in df_iperf_retx_list]) * 1.1 if df_iperf_retx_list else 1
    y_max_dropped = df_buffer_dropped['dropped_pkts'].max() * 1.1 if not df_buffer_dropped.empty else 1
    y_max_overlimits = df_buffer_overlimit['overlimits_pkts'].max() * 1.1 if not df_buffer_overlimit.empty else 1
    # if has_ecn:
    #    y_max_ecn = df_ecn_list['ECE_FLAG'].max() * 1.1 if df_ecn_list else 1

    def safe_set_ylim(ax, y_max):
        if y_max == 0:
            ax.set_ylim(0, 1)
        else:
            ax.set_ylim(0, y_max)

    # Calculate retx_df for each flow
    retx_dfs = []
    for i in range(len(df_cwnd_list)):
        retx = []
        step = 1
        interval = step
        retx_sum = 0
        retx.append([0, retx_sum])

        for index, row in df_retx_list[i].iterrows(): 
            if row['time_stamp_sec'] <= interval:
                retx_sum += row['retx_pkts']
            else:
                retx.append([interval, retx_sum])
                interval += step
                retx_sum = 0

        column_names = ['interval_sec','retx_sum_pkts']
        retx_df = pd.DataFrame(retx, columns=column_names)
        retx_dfs.append(retx_df)

    # Determine the maximum value for y-axis limits
    y_max_retx = max([df['retx_sum_pkts'].max() for df in retx_dfs]) * 1.1 if retx_dfs else 1

    for i in range(len(df_cwnd_list)):
        retx_df = retx_dfs[i]
        dst_port, src_port = df_cwnd_list[i]['dst_port'].iloc[0], df_cwnd_list[i]['src_port'].iloc[0]
        flow_label = f'Flow #{flow_counter}'  # Create a flow label

        # Add a new column 'flow_id' with the current flow counter to each DataFrame
        df_rtt_list[i]['flow_id'] = flow_counter
        retx_df['flow_id'] = flow_counter
        df_iperf_cwnd_list[i]['flow_id'] = flow_counter
        df_iperf_retx_list[i]['flow_id'] = flow_counter
        df_buffer_dropped['flow_id'] = flow_counter
        df_buffer_overlimit['flow_id'] = flow_counter
        df_probe_rtt['flow_id'] = flow_counter
        if has_ecn:
            df_ecn_list[i]['flow_id'] = flow_counter

        # Save data to separate CSV files for each type
        df_rtt_list[i][['flow_id', 'time_stamp_sec', 'rtt_ms']].to_csv(
            os.path.join(path, f'{file_name}_rtt.csv'), mode='a', header=not os.path.exists(os.path.join(path, f'{file_name}_rtt.csv')), index=False)
        retx_df[['flow_id', 'interval_sec', 'retx_sum_pkts']].to_csv(
            os.path.join(path, f'{file_name}_retx.csv'), mode='a', header=not os.path.exists(os.path.join(path, f'{file_name}_retx.csv')), index=False)
        df_iperf_cwnd_list[i][['flow_id', 'Time_sec', 'Cwnd_MBytes']].to_csv(
            os.path.join(path, f'{file_name}_iperf_cwnd.csv'), mode='a', header=not os.path.exists(os.path.join(path, f'{file_name}_iperf_cwnd.csv')), index=False)
        df_iperf_retx_list[i][['flow_id', 'Time_sec', 'Retx_pkts']].to_csv(
            os.path.join(path, f'{file_name}_iperf_retx.csv'), mode='a', header=not os.path.exists(os.path.join(path, f'{file_name}_iperf_retx.csv')), index=False)
        df_buffer_dropped[['flow_id', 'time_stamp_sec', 'dropped_pkts']].to_csv(
            os.path.join(path, f'{file_name}_buffer_dropped.csv'), mode='a', header=not os.path.exists(os.path.join(path, f'{file_name}_buffer_dropped.csv')), index=False)
        df_buffer_overlimit[['flow_id', 'time_stamp_sec', 'overlimits_pkts']].to_csv(
            os.path.join(path, f'{file_name}_buffer_overlimit.csv'), mode='a', header=not os.path.exists(os.path.join(path, f'{file_name}_buffer_overlimit.csv')), index=False)
        df_probe_rtt[['flow_id', 'time_stamp', 'rtt_ms']].to_csv(
            os.path.join(path, f'{file_name}_probe_rtt.csv'), mode='a', header=not os.path.exists(os.path.join(path, f'{file_name}_probe_rtt.csv')), index=False)
        if has_ecn:
            df_ecn_list[i][['flow_id', 'time_stamp_sec', 'ECN', 'ECE_FLAG', 'CWR_FLAG']].to_csv(
                os.path.join(path, f'{file_name}_ecn.csv'), mode='a', header=not os.path.exists(os.path.join(path, f'{file_name}_ecn.csv')), index=False)

        # Plotting data
        axs[0].plot(df_iperf_cwnd_list[i]['Time_sec'], df_iperf_cwnd_list[i]['Cwnd_MBytes'], label=f'{flow_label}')
        axs[0].set_ylabel('MBytes_iperf')
        safe_set_ylim(axs[0], y_max_iperf_cwnd)

        axs[1].plot(df_rtt_list[i]['time_stamp_sec'], df_rtt_list[i]['rtt_ms'], label=f'{flow_label}')
        axs[1].set_ylabel('rtt_msec')
        safe_set_ylim(axs[1], y_max_rtt)

        axs[2].plot(df_probe_rtt['time_stamp'], df_probe_rtt['rtt_ms'], label=f'{flow_label}', color='blue')
        axs[2].set_ylabel('probed_rtt_msec')
        safe_set_ylim(axs[2], y_max_probe_rtt)

        if has_ecn:
            axs[3].plot(df_ecn_list[i]['time_stamp_sec'], df_ecn_list[i]['ECE_FLAG'], label=f'{flow_label} ECE_FLAG', linestyle='--', color='purple')
            axs[3].set_ylabel('ECE Flags')
            safe_set_ylim(axs[3], 1.1)

        axs[3 if not has_ecn else 4].plot(retx_df['interval_sec'], retx_df['retx_sum_pkts'], label=f'{flow_label}')
        axs[3 if not has_ecn else 4].set_ylabel('retx_pkts')
        safe_set_ylim(axs[3 if not has_ecn else 4], y_max_retx)

        axs[4 if not has_ecn else 5].plot(df_iperf_retx_list[i]['Time_sec'], df_iperf_retx_list[i]['Retx_pkts'], label=f'{flow_label}')
        axs[4 if not has_ecn else 5].set_ylabel('retx_pkts_iperf')
        safe_set_ylim(axs[4 if not has_ecn else 5], y_max_iperf_retx)

        buffer_nonzero = df_buffer_dropped[df_buffer_dropped['dropped_pkts'] != 0]
        axs[5 if not has_ecn else 6].stem(buffer_nonzero['time_stamp_sec'], buffer_nonzero['dropped_pkts'], linefmt='none', 
                    markerfmt='*r', basefmt='y', bottom=0, label=f'{flow_label}')
        axs[5 if not has_ecn else 6].set_ylabel('dropped_pkts')
        safe_set_ylim(axs[5 if not has_ecn else 6], y_max_dropped)
        
        axs[6 if not has_ecn else 7].plot(df_buffer_overlimit['time_stamp_sec'], df_buffer_overlimit['overlimits_pkts'], label=f'{flow_label}', color='orange')
        axs[6 if not has_ecn else 7].set_ylabel('overlimits_pkts')
        safe_set_ylim(axs[6 if not has_ecn else 7], y_max_overlimits)
        
        flow_counter += 1  # Increment the flow counter for the next flow


    axs[6 if not has_ecn else 7].set_xlim(0, 120)  # Set x-axis limits
    axs[6 if not has_ecn else 7].set_xlabel('time_sec')
    
    # Move the legend to the upper part of the image
    # axs[0].legend(loc='lower center', bbox_to_anchor=(0.5, 1.25), ncol=6, fancybox=True, shadow=False)

    fig_name = f'{path}/{file_name}_combined.png'
    plt.savefig(fig_name, dpi=600)  # Save the plot as an image file
    plt.close()  # Close the figure to avoid overlapping plots
    
    cf.go_offline()  # Enable offline mode for cufflinks

    # Create a subplot with shared x-axis
    fig = make_subplots(rows=num_plots, cols=1, shared_xaxes=True, subplot_titles=(
        'MBytes_iperf', 'rtt_msec', 'probed_rtt_msec',
        'ECE Flags' if has_ecn else '', 'retx_pkts', 'retx_pkts_iperf', 'dropped_pkts', 'overlimits_pkts'
    ))
    
    flow_counter = 1  # Initialize the flow counter
        
    for i in range(len(df_cwnd_list)):
        dst_port, src_port = df_cwnd_list[i]['dst_port'].iloc[0], df_cwnd_list[i]['src_port'].iloc[0]
        flow_label = f'Flow #{flow_counter}'  # Create a flow label

        fig.add_trace(go.Scatter(x=df_iperf_cwnd_list[i]['Time_sec'], y=df_iperf_cwnd_list[i]['Cwnd_MBytes'],
                                 mode='lines', name=flow_label), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_rtt_list[i]['time_stamp_sec'], y=df_rtt_list[i]['rtt_ms'],
                                 mode='lines', name=flow_label), row=2, col=1)
        fig.add_trace(go.Scatter(x=df_probe_rtt['time_stamp'], y=df_probe_rtt['rtt_ms'],
                                 mode='lines', name=flow_label), row=3, col=1)
        if has_ecn:
            fig.add_trace(go.Scatter(x=df_ecn_list[i]['time_stamp_sec'], y=df_ecn_list[i]['ECE_FLAG'],
                                     mode='lines', name=f'{flow_label} ECE_FLAG', line=dict(dash='dash', color='purple')), row=4, col=1)
        fig.add_trace(go.Scatter(x=retx_df['interval_sec'], y=retx_df['retx_sum_pkts'],
                                 mode='lines', name=flow_label), row=5 if has_ecn else 4, col=1)
        fig.add_trace(go.Scatter(x=df_iperf_retx_list[i]['Time_sec'], y=df_iperf_retx_list[i]['Retx_pkts'],
                                 mode='lines', name=flow_label), row=6 if has_ecn else 5, col=1)
        buffer_trace_nonzero = df_buffer_dropped[df_buffer_dropped['dropped_pkts'] != 0]
        fig.add_trace(go.Scatter(x=buffer_trace_nonzero['time_stamp_sec'], y=buffer_trace_nonzero['dropped_pkts'],
                                 mode='markers', name=flow_label, marker=dict(symbol='star',
                                 size=8, color='red')), row=7 if has_ecn else 6, col=1)
        fig.add_trace(go.Scatter(x=df_buffer_overlimit['time_stamp_sec'], y=df_buffer_overlimit['overlimits_pkts'],
                                 mode='lines', name=flow_label, line=dict(color='orange')), row=8 if has_ecn else 7, col=1)

        flow_counter += 1  # Increment the flow counter for the next flow
    
    # Set x-axis limits
    fig.update_xaxes(range=[0, 120], row=num_plots, col=1, title_text='time_sec', dtick=10)
    
    # Set y-axis limits
    fig.update_yaxes(range=[0, y_max_iperf_cwnd], row=1, col=1)
    fig.update_yaxes(range=[0, y_max_rtt], row=2, col=1)
    fig.update_yaxes(range=[0, y_max_probe_rtt], row=3, col=1)
    if has_ecn:
        fig.update_yaxes(range=[0, None], row=4, col=1)
    fig.update_yaxes(range=[0, y_max_retx], row=5 if has_ecn else 4, col=1)
    fig.update_yaxes(range=[0, y_max_iperf_retx], row=6 if has_ecn else 5, col=1)
    fig.update_yaxes(range=[0, y_max_dropped], row=7 if has_ecn else 6, col=1)
    fig.update_yaxes(range=[0, y_max_overlimits], row=8 if has_ecn else 7, col=1)
    
    # Update the layout and titles
    fig.update_layout(title_text='Combined Data Plots', showlegend=False)
    
    # Save the plot as an HTML file
    fig_name = f'{path}/{file_name}_combined.html'
    plot(fig, filename=fig_name, auto_open=False)


def plot_df(df_extracted, df_rtt, df_retx, df_buffer_dropped, df_buffer_overlimit, df_probe_rtt, df_iperf_cwnd, 
            df_iperf_retx, path, file_name, has_ecn):
    # Initialize lists to store DataFrames
    df_cwnd_list = []
    df_rtt_list = []
    df_retx_list = []
    df_iperf_cwnd_list = []
    df_iperf_retx_list = []
    df_ecn_list = []

    # Filter the DataFrame to include only combinations with dst_port >= 15611
    df_filtered_extracted = df_extracted[(df_extracted['dst_port'] >= 15611) & (df_extracted['dst_port'] <= 15670)]
    df_filtered_rtt = df_rtt[(df_rtt['src_port'] >= 15611) & (df_rtt['src_port'] <= 15670)]
    df_filtered_retx = df_retx[(df_retx['dst_port'] >= 15611) & (df_retx['dst_port'] <= 15670)]

    # Plot combined cwnd, rtt, and retx for each combination
    for (dst_port, src_port), group_df in df_filtered_extracted.groupby(['dst_port', 'src_port']):
        if has_ecn:
            df_cwnd = group_df[['dst_port', 'src_port', 'time_stamp_sec', 'cwnd_bytes']]
            df_ecn = group_df[['dst_port', 'src_port', 'time_stamp_sec', 'ECN', 'ECE_FLAG', 'CWR_FLAG']] 
        else:
            df_cwnd = group_df[['dst_port', 'src_port', 'time_stamp_sec', 'cwnd_bytes']]

        df_rtt_group = df_filtered_rtt[(df_filtered_rtt['dst_port'] == src_port) & (df_filtered_rtt['src_port'] == dst_port)]
        df_retx_group = df_filtered_retx[(df_filtered_retx['dst_port'] == dst_port) & (df_filtered_retx['src_port'] == src_port)]
        df_iperf_cwnd_group = df_iperf_cwnd[(df_iperf_cwnd['dst_port'] == dst_port) & (df_iperf_cwnd['src_port'] == src_port)]
        df_iperf_retx_group = df_iperf_retx[(df_iperf_retx['dst_port'] == dst_port) & (df_iperf_retx['src_port'] == src_port)]

        if not df_cwnd.empty and not df_rtt_group.empty and not df_iperf_cwnd_group.empty:
            df_cwnd_list.append(df_cwnd)
            df_rtt_list.append(df_rtt_group)
            df_retx_list.append(df_retx_group)
            df_iperf_cwnd_list.append(df_iperf_cwnd_group)
            df_iperf_retx_list.append(df_iperf_retx_group)
            if has_ecn:
                df_ecn_list.append(df_ecn) 
        
    # Call the function to plot combined data
    plot_combined_data(df_cwnd_list, df_rtt_list, df_retx_list, df_iperf_cwnd_list, 
                       df_iperf_retx_list, df_buffer_dropped, df_buffer_overlimit, df_probe_rtt, df_ecn_list, path, file_name, has_ecn)

# Main script
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

aqm_config = ["fifo", "fq_codel", "red"]

bdp_config = [1, 2, 4]

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

                    s1 = f"/data2/imtiaz/bbrv3_new/poseidon-sender-1_output/output/{speed['tag']}_{cca_combo['cca1']}_{cca_combo['cca2']}_{aqm}_{bdp}bdp_{run}"
                    s2 = f"/data2/imtiaz/bbrv3_new/poseidon-sender-2_output/output/{speed['tag']}_{cca_combo['cca2']}_{cca_combo['cca1']}_{aqm}_{bdp}bdp_{run}"
                    r1 = f"/data2/imtiaz/bbrv3_new/poseidon-router-1_output/output/{speed['tag']}_{cca_combo['cca1']}_{cca_combo['cca2']}_{aqm}_{bdp}bdp_{run}_buffer"
                    
                    # Select appropriate buffer file based on AQM
                    if aqm == "fq_codel":
                        buffer_file_r1 = f"{r1}/buffer_status_fq_codel.csv"
                    elif aqm == "red":
                        buffer_file_r1 = f"{r1}/buffer_status_red.csv"
                    else:
                        buffer_file_r1 = f"{r1}/buffer_status.csv"
                    
                    file_name_s1 = f"sender_1_{speed['tag']}_{cca_combo['cca1']}_{cca_combo['cca2']}_{aqm}_{bdp}bdp_{run}"
                    file_name_s2 = f"sender_2_{speed['tag']}_{cca_combo['cca2']}_{cca_combo['cca1']}_{aqm}_{bdp}bdp_{run}"
                    
                    # sender 1
                    s1_command = f'python3 /data2/imtiaz/bbrv3_new/process_iperf.py {s1}'
                    subprocess.run(s1_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    # sender 2
                    s2_command = f'python3 /data2/imtiaz/bbrv3_new/process_iperf.py {s2}'
                    subprocess.run(s2_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)           

                    # Ensure all necessary files exist and are not empty
                    files_to_check = [
                        f"{s1}/extracted_information.csv", f"{s1}/rtt.csv", f"{s1}/retx.csv", f"{s1}/ping_active_rtt.csv", f"{s1}/iperf_data.csv",
                        f"{s2}/extracted_information.csv", f"{s2}/rtt.csv", f"{s2}/retx.csv", f"{s2}/ping_active_rtt.csv", f"{s2}/iperf_data.csv",
                        buffer_file_r1
                    ]
                    
                    all_files_exist = all(os.path.exists(f) for f in files_to_check)
                    all_files_nonempty = all(os.path.getsize(f) > 0 for f in files_to_check)

                    if not all_files_exist or not all_files_nonempty:
                        print(f"Skipping due to missing or empty files in configuration: {row}")
                        continue

                    # Read data from the s1 files
                    extracted_info_file_s1 = f"{s1}/extracted_information.csv"
                    rtt_file_s1 = f"{s1}/rtt.csv"
                    retx_file_s1 = f"{s1}/retx.csv"
                    prob_rtt_file_s1 = f"{s1}/ping_active_rtt.csv"
                    iperf_file_s1 = f"{s1}/iperf_data.csv"

                    # Read data from the s2 files
                    extracted_info_file_s2 = f"{s2}/extracted_information.csv"
                    rtt_file_s2 = f"{s2}/rtt.csv"
                    retx_file_s2 = f"{s2}/retx.csv"
                    prob_rtt_file_s2 = f"{s2}/ping_active_rtt.csv"
                    iperf_file_s2 = f"{s2}/iperf_data.csv"

                    
                    # Preprocess the data from the s1 file
                    df_extracted_s1, first_timestamp_s1 = read_and_preprocess(extracted_info_file_s1)
                    df_rtt_s1 = process_rtt_and_retx(rtt_file_s1, first_timestamp_s1)
                    df_retx_s1 = process_rtt_and_retx(retx_file_s1, first_timestamp_s1)
                    df_probe_rtt_s1 = process_probe_rtt(prob_rtt_file_s1, first_timestamp_s1)
                    df_iperf_cwnd_s1, df_iperf_retx_s1 = process_iperf_data(iperf_file_s1)

                    # Preprocess the data from the s2 files
                    df_extracted_s2, first_timestamp_s2 = read_and_preprocess(extracted_info_file_s2)
                    df_rtt_s2 = process_rtt_and_retx(rtt_file_s2, first_timestamp_s1)
                    df_retx_s2 = process_rtt_and_retx(retx_file_s2, first_timestamp_s1)
                    df_probe_rtt_s2 = process_probe_rtt(prob_rtt_file_s2, first_timestamp_s1)
                    df_iperf_cwnd_s2, df_iperf_retx_s2 = process_iperf_data(iperf_file_s2)

                    
                    print(f"df_iperf_cwnd_list head sender 1:\n", df_iperf_cwnd_s1.head())
                    print(f"df_iperf_cwnd_list head sender 2:\n", df_iperf_cwnd_s2.head())

                    # Preprocess the data from the r1 files
                    df_buffer_dropped_r1, df_buffer_overlimit_r1 = process_buffer(buffer_file_r1, first_timestamp_s1)

                    # Plot the data from the s1 files
                    if df_extracted_s1 is not None and df_rtt_s1 is not None and df_retx_s1 is not None:
                        plot_df(df_extracted_s1, df_rtt_s1, df_retx_s1, df_buffer_dropped_r1, df_buffer_overlimit_r1, 
                                df_probe_rtt_s1, df_iperf_cwnd_s1, df_iperf_retx_s1, s1, file_name_s1, has_ecn)

                    # Plot the data from the s2 files
                    if df_extracted_s2 is not None and df_rtt_s2 is not None and df_retx_s2 is not None:
                        plot_df(df_extracted_s2, df_rtt_s2, df_retx_s2, df_buffer_dropped_r1, df_buffer_overlimit_r1, 
                                df_probe_rtt_s2, df_iperf_cwnd_s2, df_iperf_retx_s2, s2, file_name_s2, has_ecn)

print("Processing completed.")