

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
