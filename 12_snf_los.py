

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