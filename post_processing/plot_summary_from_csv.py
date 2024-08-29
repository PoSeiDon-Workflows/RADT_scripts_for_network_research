import pandas as pd
import matplotlib.pyplot as plt

# Function to read and prepare data from CSV files
def prepare_data(file_path, aqm_label):
    df = pd.read_csv(file_path)
    df['AQM'] = aqm_label
    return df

# Define file paths and corresponding AQM labels
files = {
    'FIFO': '/data2/imtiaz/bbrv3_new/parsed_data/fairness_varpi_vertheta_fifo_lines.csv',
    'RED': '/data2/imtiaz/bbrv3_new/parsed_data/fairness_varpi_vertheta_red_lines.csv',
    'FQ_CODEL': '/data2/imtiaz/bbrv3_new/parsed_data/fairness_varpi_vertheta_fq_codel_lines.csv'
}

# Read and concatenate data from all files
dataframes = [prepare_data(file, aqm) for aqm, file in files.items()]
df = pd.concat(dataframes, ignore_index=True)

# Convert all columns to numeric where appropriate
for col in df.columns:
    if col not in ['CCA1', 'CCA2', 'Bandwidth', 'AQM']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Cap the values of vertheta and Jindex at 1
for col in ['1BDP_vertheta', '2BDP_vertheta', '4BDP_vertheta', '1BDP_Fairness_Index', '2BDP_Fairness_Index', '4BDP_Fairness_Index']:
    df[col] = df[col].clip(upper=1)

# Create separate DataFrames for each BDP setup
df_1bdp = df[['CCA1', 'CCA2', 'AQM', '1BDP_Fairness_Index', '1BDP_varpi', '1BDP_vertheta']].copy()
df_1bdp.columns = ['CCA1', 'CCA2', 'AQM', 'Fairness_Index', 'varpi', 'vertheta']
df_1bdp['BDP'] = '1xBDP'

df_2bdp = df[['CCA1', 'CCA2', 'AQM', '2BDP_Fairness_Index', '2BDP_varpi', '2BDP_vertheta']].copy()
df_2bdp.columns = ['CCA1', 'CCA2', 'AQM', 'Fairness_Index', 'varpi', 'vertheta']
df_2bdp['BDP'] = '2xBDP'

df_4bdp = df[['CCA1', 'CCA2', 'AQM', '4BDP_Fairness_Index', '4BDP_varpi', '4BDP_vertheta']].copy()
df_4bdp.columns = ['CCA1', 'CCA2', 'AQM', 'Fairness_Index', 'varpi', 'vertheta']
df_4bdp['BDP'] = '4xBDP'

# Combine the DataFrames
df_combined = pd.concat([df_1bdp, df_2bdp, df_4bdp], ignore_index=True)

# Calculate averages, excluding non-numeric columns
numeric_columns = df_combined.columns.drop(['CCA1', 'CCA2', 'AQM', 'BDP'])
df_avg = df_combined.groupby(['CCA1', 'CCA2', 'AQM', 'BDP'])[numeric_columns].mean().reset_index()

# Convert CCA names to uppercase for x-axis labels
df_avg['CCA_Comparison'] = df_avg['CCA1'].str.upper() + ' vs ' + df_avg['CCA2'].str.upper()

# Define a mapping for the subplot titles
titles = {
    'FIFO-1xBDP': '(a) FIFO - 1 x BDP',
    'RED-1xBDP': '(b) RED - 1 x BDP',
    'FQ_CODEL-1xBDP': '(c) FQ_CoDel - 1 x BDP',
    'FIFO-2xBDP': '(d) FIFO - 2 x BDP',
    'RED-2xBDP': '(e) RED - 2 x BDP',
    'FQ_CODEL-2xBDP': '(f) FQ_CoDel - 2 x BDP',
    'FIFO-4xBDP': '(g) FIFO - 4 x BDP',
    'RED-4xBDP': '(h) RED - 4 x BDP',
    'FQ_CODEL-4xBDP': '(i) FQ_CoDel - 4 x BDP'
}

# Create a figure to hold all subplots
fig, axes = plt.subplots(3, 3, figsize=(24, 18))

# Flatten axes array for easy iteration
axes = axes.flatten()

# Ensure proper order of groups
order = [
    'FIFO-1xBDP', 'RED-1xBDP', 'FQ_CODEL-1xBDP', 
    'FIFO-2xBDP', 'RED-2xBDP', 'FQ_CODEL-2xBDP', 
    'FIFO-4xBDP', 'RED-4xBDP', 'FQ_CODEL-4xBDP'
]
grouped = df_avg.groupby(['AQM', 'BDP'], sort=False)
sorted_groups = [grouped.get_group((aqm.split('-')[0], aqm.split('-')[1])) for aqm in order]

# Plot performances for each AQM and BDP
for idx, group in enumerate(sorted_groups):
    aqm = order[idx]
    ax1 = axes[idx]
    
    # First axis (left y-axis for vertheta)
    # ax1.set_xlabel('Comparison', fontsize=15)
    ax1.set_ylabel(r'$\mathrm{Avg}(\theta)$', fontsize=18, color='tab:red')  # Using LaTeX for theta symbol
    ax1.scatter(group['CCA_Comparison'], group['vertheta'], color='red', marker='o', s=100, label=rf'$\mathrm{{Avg}}(\theta)$')
    ax1.set_ylim(0, 1)
    ax1.tick_params(axis='y', labelcolor='tab:red')
    ax1.tick_params(axis='x', labelrotation=45)
    
    # Second axis (right y-axis for fairness index)
    ax2 = ax1.twinx()
    ax2.set_ylabel(r'$\mathrm{Avg}(J_{\mathrm{index}})$', fontsize=18, color='tab:blue')  # Using LaTeX for J_index symbol
    ax2.scatter(group['CCA_Comparison'], group['Fairness_Index'], color='blue', marker='s', s=100, label=r'$\mathrm{{Avg}}(J_{\mathrm{index}})$')
    ax2.set_ylim(0, 1)
    ax2.tick_params(axis='y', labelcolor='tab:blue')
    
    # Third axis for varpi
    ax3 = ax1.twinx()
    ax3.set_ylabel(r'$\mathrm{Avg}(\varpi)$', fontsize=18, color='tab:green')  # Using LaTeX for varpi symbol
    ax3.scatter(group['CCA_Comparison'], group['varpi'], color='green', marker='^', s=100, label=r'$\mathrm{{Avg}}(\varpi)$')
    ax3.tick_params(axis='y', labelcolor='tab:green')
    ax3.spines['right'].set_position(('outward', 60))
    
    # Add a legend combining information from all axes
    handles, labels = [], []
    for ax in [ax1, ax2, ax3]:
        h, l = ax.get_legend_handles_labels()
        handles.extend(h)
        labels.extend(l)
    ax1.legend(handles, labels, loc='best', fontsize=10)
    
    # Set the title for the subplot using the titles mapping
    ax1.set_title(titles[aqm], fontsize=14)

# Adjust the layout to prevent overlapping
plt.tight_layout()

# Use a local path for saving the figure
local_save_path = "/data2/imtiaz/bbrv3_new/parsed_data/combined_figure.png"

# Save the figure to your local path
plt.savefig(local_save_path, dpi=600, bbox_inches='tight')

# Show the plot
# plt.show()
