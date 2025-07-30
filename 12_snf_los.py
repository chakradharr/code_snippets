

# Define thresholds
short_los_threshold = 10
long_los_threshold = 20

# Create flags
df_clean['short_stay_flag'] = df_clean['length_of_stay'] <= short_los_threshold
df_clean['long_stay_flag'] = df_clean['length_of_stay'] >= long_los_threshold

# Aggregate cumulative % of long and short stays per decile
los_percent_summary = df_clean.groupby("risk_decile").agg(
    total=('length_of_stay', 'count'),
    long_stay_pct=('long_stay_flag', 'mean'),
    short_stay_pct=('short_stay_flag', 'mean')
).reset_index()

# Convert to percentages
los_percent_summary['long_stay_pct'] *= 100
los_percent_summary['short_stay_pct'] *= 100



import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(14, 6))

# Plot Long Stay %
plt.subplot(1, 2, 1)
sns.barplot(data=los_percent_summary, x='risk_decile', y='long_stay_pct', palette='Reds')
plt.title(f'Cumulative % of LOS ≥ {long_los_threshold} Days by Risk Decile')
plt.ylabel('% of Long Stays')
plt.xlabel('Risk Decile')

# Plot Short Stay %
plt.subplot(1, 2, 2)
sns.barplot(data=los_percent_summary, x='risk_decile', y='short_stay_pct', palette='Blues')
plt.title(f'Cumulative % of LOS ≤ {short_los_threshold} Days by Risk Decile')
plt.ylabel('% of Short Stays')
plt.xlabel('Risk Decile')

plt.tight_layout()
plt.show()




import pandas as pd
import numpy as np

# Ensure 'length_of_stay' is numeric
df_clean['length_of_stay'] = pd.to_numeric(df_clean['length_of_stay'], errors='coerce')

# Create SNF Risk Score Deciles (if not already created)
df_clean["risk_decile"] = pd.qcut(df_clean["snf_score_new"], q=10, labels=[f'D{i+1}' for i in range(10)])

# Define stay flags
df_clean['short_stay_flag'] = df_clean['length_of_stay'] <= 10
df_clean['long_stay_flag'] = df_clean['length_of_stay'] >= 20

# Group by decile and compute total + % of short and long stays
los_percent_summary = df_clean.groupby("risk_decile").agg(
    total=('length_of_stay', 'count'),
    long_stay_pct=('long_stay_flag', 'mean'),
    short_stay_pct=('short_stay_flag', 'mean')
).reset_index()

# Convert to percentages
los_percent_summary['long_stay_pct'] = (los_percent_summary['long_stay_pct'] * 100).round(1)
los_percent_summary['short_stay_pct'] = (los_percent_summary['short_stay_pct'] * 100).round(1)

# Display the summary
print(los_percent_summary)

# Optional: Save to Excel
los_percent_summary.to_excel("los_cumulative_pct_by_decile.xlsx", index=False)




### 0617

import pandas as pd

def get_metrics_grid(df, score_col='rap_score', los_col='snf_los',
                     los_thresholds=range(7, 21), score_cutoffs=[0.3, 0.4, 0.5, 0.6, 0.7]):
    """
    Computes classification metrics (TP, FP, FN, TN, Sensitivity, Specificity, PPV, NPV, Accuracy, Lift)
    for each combination of LOS threshold and score cutoff.

    Parameters:
    - df: DataFrame
    - score_col: Column with prediction score
    - los_col: Column with SNF LOS
    - los_thresholds: List or range of LOS thresholds to evaluate
    - score_cutoffs: List of score cutoffs to evaluate

    Returns:
    - DataFrame with all metrics for each LOS threshold and cutoff
    """
    results = []

    for los_thresh in los_thresholds:
        df['y_true'] = (df[los_col] >= los_thresh).astype(int)

        for cutoff in score_cutoffs:
            df['y_pred'] = (df[score_col] >= cutoff).astype(int)

            tp = ((df['y_pred'] == 1) & (df['y_true'] == 1)).sum()
            tn = ((df['y_pred'] == 0) & (df['y_true'] == 0)).sum()
            fp = ((df['y_pred'] == 1) & (df['y_true'] == 0)).sum()
            fn = ((df['y_pred'] == 0) & (df['y_true'] == 1)).sum()

            sensitivity = round(tp / (tp + fn), 2) if (tp + fn) else None
            specificity = round(tn / (tn + fp), 2) if (tn + fp) else None
            ppv = round(tp / (tp + fp), 2) if (tp + fp) else None
            npv = round(tn / (tn + fn), 2) if (tn + fn) else None
            accuracy = round((tp + tn) / (tp + tn + fp + fn), 2)
            lift = round((tp / (tp + fp)) / ((tp + fn) / (tp + tn + fp + fn)), 2) if (tp + fp) and (tp + fn) else None

            results.append({
                'LOS_Threshold': los_thresh,
                'Score_Cutoff': cutoff,
                'TP': tp,
                'FP': fp,
                'FN': fn,
                'TN': tn,
                'Sensitivity': sensitivity,
                'Specificity': specificity,
                'PPV': ppv,
                'NPV': npv,
                'Accuracy': accuracy,
                'Lift': lift
            })

    return pd.DataFrame(results)
    
metrics_grid_df = get_metrics_grid(
    df,
    score_col='rap_score',
    los_col='snf_los',
    los_thresholds=range(7, 21),
    score_cutoffs=[0.3, 0.4, 0.5, 0.6, 0.7]
)

## 0617 graphs

import matplotlib.pyplot as plt
import seaborn as sns

def plot_sensitivity_specificity(metrics_df, los_thresholds=[7, 10, 14]):
    for threshold in los_thresholds:
        data = metrics_df[metrics_df['LOS_Threshold'] == threshold]

        plt.figure(figsize=(10, 5))
        plt.plot(data['Score_Cutoff'], data['Sensitivity'], marker='o', label='Sensitivity')
        plt.plot(data['Score_Cutoff'], data['Specificity'], marker='o', label='Specificity')
        plt.title(f'Sensitivity vs. Specificity for LOS ≥ {threshold} Days')
        plt.xlabel('RAP Score Cutoff')
        plt.ylabel('Metric Value')
        plt.ylim(0, 1)
        plt.grid(True)
        plt.legend()
        plt.show()
        
        
def plot_ppv_npv_accuracy(metrics_df, los_thresholds=[7, 10, 14]):
    for threshold in los_thresholds:
        data = metrics_df[metrics_df['LOS_Threshold'] == threshold]

        plt.figure(figsize=(10, 5))
        plt.plot(data['Score_Cutoff'], data['PPV'], marker='o', label='PPV')
        plt.plot(data['Score_Cutoff'], data['NPV'], marker='o', label='NPV')
        plt.plot(data['Score_Cutoff'], data['Accuracy'], marker='o', label='Accuracy')
        plt.title(f'PPV, NPV, Accuracy for LOS ≥ {threshold} Days')
        plt.xlabel('RAP Score Cutoff')
        plt.ylabel('Metric Value')
        plt.ylim(0, 1)
        plt.grid(True)
        plt.legend()
        plt.show()
        
def plot_lift(metrics_df, los_thresholds=[7, 10, 14]):
    for threshold in los_thresholds:
        data = metrics_df[metrics_df['LOS_Threshold'] == threshold]

        plt.figure(figsize=(10, 5))
        plt.plot(data['Score_Cutoff'], data['Lift'], marker='o', label='Lift', color='purple')
        plt.title(f'Lift vs. Score Cutoff for LOS ≥ {threshold} Days')
        plt.xlabel('RAP Score Cutoff')
        plt.ylabel('Lift')
        plt.grid(True)
        plt.legend()
        plt.show()
        
        
plot_sensitivity_specificity(metrics_grid_df)
plot_ppv_npv_accuracy(metrics_grid_df)
plot_lift(metrics_grid_df)

# visualize cutoff 

# Add Youden’s J to existing metrics grid
metrics_grid_df['Youdens_J'] = metrics_grid_df['Sensitivity'] + metrics_grid_df['Specificity'] - 1

best_cutoffs = (
    metrics_grid_df
    .sort_values(['LOS_Threshold', 'Youdens_J'], ascending=[True, False])
    .groupby('LOS_Threshold')
    .head(1)
    .reset_index(drop=True)
)

print(best_cutoffs)

import matplotlib.pyplot as plt

def plot_youden(metrics_df, los_thresholds=[7, 10, 14]):
    for threshold in los_thresholds:
        data = metrics_df[metrics_df['LOS_Threshold'] == threshold]

        plt.figure(figsize=(10, 5))
        plt.plot(data['Score_Cutoff'], data['Youdens_J'], marker='o', label="Youden's J")
        plt.title(f"Youden’s J vs Score Cutoff for LOS ≥ {threshold} Days")
        plt.xlabel('RAP Score Cutoff')
        plt.ylabel("Youden's J")
        plt.grid(True)
        plt.legend()
        plt.show()
        
plot_youden(metrics_grid_df)



def get_score_decile_cutoffs(df, score_col='rap_score'):
    """
    Returns the cutoff values for each decile of the score.
    Shows min/max score within each decile.
    """
    df = df.copy()
    df['decile'] = pd.qcut(df[score_col], 10, labels=False) + 1  # 1 = lowest, 10 = highest

    decile_summary = (
        df.groupby('decile')[score_col]
        .agg(['min', 'max'])
        .rename(columns={'min': 'score_min', 'max': 'score_max'})
        .reset_index()
    )

    return decile_summary

decile_cutoffs = get_score_decile_cutoffs(df, score_col='rap_score')
print(decile_cutoffs)


######## 06/24

import pandas as pd
import matplotlib.pyplot as plt

# Assuming your DataFrame is named df
# df = pd.read_csv("your_file.csv")  # Or however you're loading it

# Convert to datetime
df['score_eff_dt'] = pd.to_datetime(df['score_eff_dt'])
df['admit_dt'] = pd.to_datetime(df['admit_dt'])

# Calculate days between score and admit
df['days_before_admit'] = (df['admit_dt'] - df['score_eff_dt']).dt.days

# Basic statistics
print("Summary statistics:")
print(df['days_before_admit'].describe())

# Distribution plot
plt.figure(figsize=(10, 6))
plt.hist(df['days_before_admit'], bins=30, edgecolor='black')
plt.title('Distribution of Days Between Score and Admit Date')
plt.xlabel('Days Before Admit Date (score_eff_dt - admit_dt)')
plt.ylabel('Number of Patients')
plt.grid(True)
plt.show()



### 0625

import pandas as pd
import matplotlib.pyplot as plt

# Assume df['days_before_admit'] is already created

plt.figure(figsize=(10, 6))

# Plot histogram as percentages
counts, bins, patches = plt.hist(df['days_before_admit'], bins=30, edgecolor='black', density=True)

# Convert y-axis to percentage
plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y * 100:.1f}%'))

plt.title('Distribution of Days Between Score and Admit Date (as %)')
plt.xlabel('Days Before Admit Date (score_eff_dt - admit_dt)')
plt.ylabel('Percentage of Patients')
plt.xlim(-10, 20)  # Focus on range of interest
plt.grid(True)
plt.show()

#### 0626

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Assume df['days_before_admit'] already exists

# Define bins (customize as needed)
bins = np.arange(-10, 21, 2)  # bins from -10 to 20 with step size 2

# Bin the data
counts, bin_edges = np.histogram(df['days_before_admit'], bins=bins)

# Convert counts to percentages
percentages = counts / counts.sum() * 100

# Midpoints for plotting
bin_midpoints = (bin_edges[:-1] + bin_edges[1:]) / 2

# Plot
plt.figure(figsize=(10, 6))
plt.bar(bin_midpoints, percentages, width=1.8, edgecolor='black')

plt.title('Percentage of Patients by Days Between Score and Admit Date')
plt.xlabel('Days Before Admit Date (score_eff_dt - admit_dt)')
plt.ylabel('Percentage of Patients')
plt.xticks(bin_edges)
plt.grid(True)
plt.show()



#### 0628
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Assume df['days_before_admit'] already exists

# Define bins (customize as needed)
bins = np.arange(-10, 21, 2)  # from -10 to 20 days, 2-day width

# Create histogram
counts, bin_edges = np.histogram(df['days_before_admit'], bins=bins)
bin_midpoints = (bin_edges[:-1] + bin_edges[1:]) / 2

# Plot
plt.figure(figsize=(10, 6))
bars = plt.bar(bin_midpoints, counts, width=1.8, edgecolor='black', color='skyblue')

# Add value labels on top of each bar
for bar in bars:
    height = bar.get_height()
    if height > 0:
        plt.text(bar.get_x() + bar.get_width()/2, height + 500, f'{height:,}', 
                 ha='center', va='bottom', fontsize=9)

plt.title('Number of Patients by Days Between Score and Admit Date')
plt.xlabel('Days Before Admit Date (score_eff_dt - admit_dt)')
plt.ylabel('Number of Patients')
plt.xticks(bin_edges)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

import pandas as pd

# Rename 'rap_score' to 'snf_score'
df.rename(columns={'rap_score': 'snf_score'}, inplace=True)

# Ensure dates are in datetime format
df['admit_date'] = pd.to_datetime(df['admit_date'])
df['discharge_date'] = pd.to_datetime(df['discharge_date'])

# Compute LOS as (discharge - admit + 1)
df['los'] = (df['discharge_date'] - df['admit_date']).dt.days + 1

####0626

import matplotlib.pyplot as plt
import numpy as np

# Define bin edges manually from -35 to +5 (every 1 day)
bin_edges = np.arange(-35, 6, 1)

# Plot histogram as percentages
plt.figure(figsize=(12, 6))
n, bins, patches = plt.hist(
    filtered_df['days_before_admit'],
    bins=bin_edges,
    edgecolor='black',
    color='skyblue',
    density=True
)

# Convert frequencies to percentages
percentages = n * 100
for patch, pct in zip(patches, percentages):
    patch.set_height(pct)

# Vertical line at day 0
plt.axvline(x=0, color='red', linestyle='--', label='Admit Date (0 days)')

# Axis labels and title
plt.title('Percentage Distribution of Days (Score Eff Date vs Admit Date)', fontsize=14)
plt.xlabel('Days Before Admit (Positive = Scored Before Admission)', fontsize=12)
plt.ylabel('Percentage of Members (%)', fontsize=12)
plt.xticks(np.arange(-35, 6, 5))  # Clean x-axis ticks
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()




#### 0711

df = client.query(sql).result().to_dataframe(progress_bar_type='tqdm')

from google.cloud import bigquery
from google.cloud import bigquery_storage
from google.auth import default

credentials, project_id = default()
bq_client = bigquery.Client(credentials=credentials, project=project_id)
bq_storage_client = bigquery_storage.BigQueryReadClient(credentials=credentials)

query = """SELECT * FROM `your_project.your_dataset.your_table`"""  # Your actual query
query_job = bq_client.query(query)

# Stream efficiently using BigQuery Storage API
df = query_job.result().to_dataframe(bqstorage_client=bq_storage_client)


### added progress bar 


from google.cloud import bigquery
from google.cloud import bigquery_storage_v1
from google.auth import default
from tqdm import tqdm
import pandas as pd

credentials, project_id = default()
bq_client = bigquery.Client(credentials=credentials, project=project_id)
bq_storage_client = bigquery_storage_v1.BigQueryReadClient(credentials=credentials)

query = """SELECT * FROM `your_project.your_dataset.your_table`"""
query_job = bq_client.query(query)
query_job.result()  # Wait for job to finish

# Get reference to destination table
destination = query_job.destination
table_ref = destination.to_bqstorage()

# Create read session with parallel streams
session = bq_storage_client.create_read_session(
    parent=f"projects/{project_id}",
    read_session=bigquery_storage_v1.types.ReadSession(
        table=table_ref,
        data_format=bigquery_storage_v1.types.DataFormat.ARROW,
    ),
    max_stream_count=10,  # Controls parallelism; adjust for your machine
)

# Monitor progress across streams
dfs = []
for stream in tqdm(session.streams, desc="Downloading streams"):
    reader = bq_storage_client.read_rows(stream.name)
    dfs.append(reader.to_dataframe())

# Concatenate all partitions
df = pd.concat(dfs, ignore_index=True)




#### 0711


import pandas as pd
import numpy as np

def get_metrics_by_percentiles(df, score_col='rap_score', los_col='snf_los', los_threshold=10, percentiles=[5, 10, 15, 20, 25]):
    results = []

    for perc in percentiles:
        score_cutoff = np.percentile(df[score_col], perc)
        y_true = (df[los_col] <= los_threshold).astype(int)
        y_pred = (df[score_col] <= score_cutoff).astype(int)  # "low" scores for short LOS

        tp = ((y_true == 1) & (y_pred == 1)).sum()
        tn = ((y_true == 0) & (y_pred == 0)).sum()
        fp = ((y_true == 0) & (y_pred == 1)).sum()
        fn = ((y_true == 1) & (y_pred == 0)).sum()

        sensitivity = round(tp / (tp + fn), 2) if (tp + fn) else None
        specificity = round(tn / (tn + fp), 2) if (tn + fp) else None
        ppv = round(tp / (tp + fp), 2) if (tp + fp) else None
        npv = round(tn / (tn + fn), 2) if (tn + fn) else None
        accuracy = round((tp + tn) / (tp + tn + fp + fn), 2)
        lift = round((ppv / ((tp + fp) / len(df))), 2) if (tp + fp) else None
        identified = round(((tp + fp) / len(df)) * 100, 2)

        results.append({
            'Percentile': f'Top {perc}%',
            'Score Cutoff': round(score_cutoff, 2),
            'Sensitivity': sensitivity,
            'Specificity': specificity,
            'PPV': ppv,
            'NPV': npv,
            'Accuracy': accuracy,
            'Lift': lift,
            '% Identified': identified
        })

    return pd.DataFrame(results)
    
    
### grpah

import pandas as pd
import matplotlib.pyplot as plt

# Manually enter the data
data = {
    'RAP Score Cutoff': [22.05, 24.67, 27.68, 31.48, 36.03, 41.89],
    'Sensitivity': [0.37, 0.32, 0.27, 0.21, 0.16, 0.11],
    'Specificity': [0.66, 0.71, 0.76, 0.81, 0.86, 0.91],
    'PPV': [0.38, 0.38, 0.38, 0.38, 0.38, 0.39],
    'Accuracy': [0.56, 0.57, 0.58, 0.60, 0.61, 0.62]
}

df = pd.DataFrame(data)

# Plot
plt.figure(figsize=(10, 6))
plt.plot(df['RAP Score Cutoff'], df['Sensitivity'], marker='o', label='Sensitivity')
plt.plot(df['RAP Score Cutoff'], df['Specificity'], marker='o', label='Specificity')
plt.plot(df['RAP Score Cutoff'], df['PPV'], marker='o', label='PPV')
plt.plot(df['RAP Score Cutoff'], df['Accuracy'], marker='o', label='Accuracy')

# Add vertical threshold line at Top 20% (RAP Score ~36.03)
threshold = 36.03
plt.axvline(x=threshold, color='red', linestyle='--', linewidth=1.5, label='Top 20% Threshold')
plt.text(threshold + 0.3, 0.45, f'Top 20%\n({threshold})', color='red', fontsize=9)

# Labels and formatting
plt.xlabel('RAP Score Cutoff')
plt.ylabel('Metric Value')
plt.title('Evaluating RAP Score for Predicting Long SNF Stays (LOS ≥ 20 Days)')
plt.ylim(0, 1)
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()



-- Simulate table_a with duplicates and NULLs
WITH table_a AS (
  SELECT 1 AS individual_id UNION ALL
  SELECT 1 UNION ALL
  SELECT 2 UNION ALL
  SELECT NULL
),

-- Simulate table_b with duplicates and NULLs
table_b AS (
  SELECT 2 AS individual_id UNION ALL
  SELECT 3 UNION ALL
  SELECT 3 UNION ALL
  SELECT NULL
),

-- Step 1: LEFT JOIN table_a to table_b
cte_c AS (
  SELECT a.individual_id
  FROM table_a a
  LEFT JOIN table_b b
    ON a.individual_id = b.individual_id
)

-- Step 2: LEFT JOIN cte_c to table_a again and check for missing matches
SELECT c.individual_id
FROM cte_c c
LEFT JOIN table_a d
  ON c.individual_id = d.individual_id
WHERE d.individual_id IS NULL;
