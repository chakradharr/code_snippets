import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr, pearsonr

# Optional: high resolution for plots
sns.set(style="whitegrid")
plt.rcParams["figure.dpi"] = 120

# ---------------------------
# Step 1: Simulated Data (replace with your actual DataFrame)
# ---------------------------
np.random.seed(42)
n = 1000
df = pd.DataFrame({
    "snf_score_new": np.clip(np.random.beta(2, 5, size=n), 0, 1),
    "length_of_stay": np.random.gamma(5, 2, size=n).astype(int),
    "readmit_flag": np.random.binomial(1, 0.3, size=n)
})

# ---------------------------
# Step 2: Remove Outliers on LOS using IQR
# ---------------------------
q1 = df["length_of_stay"].quantile(0.25)
q3 = df["length_of_stay"].quantile(0.75)
iqr = q3 - q1
lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr
df_clean = df[(df["length_of_stay"] >= lower) & (df["length_of_stay"] <= upper)].copy()

# ---------------------------
# Step 3: Create Deciles on SNF Risk Score
# ---------------------------
df_clean["risk_decile"] = pd.qcut(df_clean["snf_score_new"], q=10, labels=[f'D{i+1}' for i in range(10)])

# ---------------------------
# Step 4: Correlation Calculation
# ---------------------------
spearman_corr, _ = spearmanr(df_clean["snf_score_new"], df_clean["length_of_stay"])
pearson_corr, _ = pearsonr(df_clean["snf_score_new"], df_clean["length_of_stay"])
print("Spearman:", spearman_corr)
print("Pearson :", pearson_corr)

# ---------------------------
# Step 5: Summary Table
# ---------------------------
summary = df_clean.groupby("risk_decile").agg(
    median_los=("length_of_stay", "median"),
    mean_los=("length_of_stay", "mean"),
    readmit_rate=("readmit_flag", "mean"),
    count=("readmit_flag", "count")
).reset_index()

# Save to Excel
summary.to_excel("snf_summary_stats.xlsx", index=False)

# ---------------------------
# Step 6: Visualization
# ---------------------------
plt.figure(figsize=(14, 10))

# Boxplot
plt.subplot(2, 2, 1)
sns.boxplot(data=df_clean, x="risk_decile", y="length_of_stay")
plt.title("Boxplot of LOS by SNF Risk Score Decile")

# Median LOS barplot
plt.subplot(2, 2, 2)
sns.barplot(data=summary, x="risk_decile", y="median_los")
plt.title("Median LOS by Risk Decile")

# Scatterplot
plt.subplot(2, 2, 3)
sns.scatterplot(data=df_clean, x="snf_score_new", y="length_of_stay", alpha=0.5)
plt.title("Scatterplot: SNF Risk Score vs LOS")

# Readmit rate barplot
plt.subplot(2, 2, 4)
sns.barplot(data=summary, x="risk_decile", y="readmit_rate")
plt.title("Readmission Rate by Risk Decile")
plt.ylabel("Readmit Rate")

plt.tight_layout()
plt.savefig("snf_visuals_summary.png", dpi=300)
plt.show()


# Create separate summaries by readmission status
summary_readmit = df_clean[df_clean.readmit_flag == 1].groupby("risk_decile").agg(
    median_los=("length_of_stay", "median"),
    mean_los=("length_of_stay", "mean"),
    count=("length_of_stay", "count")
).reset_index()
summary_readmit["readmit_flag"] = 1

summary_no_readmit = df_clean[df_clean.readmit_flag == 0].groupby("risk_decile").agg(
    median_los=("length_of_stay", "median"),
    mean_los=("length_of_stay", "mean"),
    count=("length_of_stay", "count")
).reset_index()
summary_no_readmit["readmit_flag"] = 0

# Combine for plotting
summary_strat = pd.concat([summary_readmit, summary_no_readmit], ignore_index=True)

# Save to Excel with multiple sheets
with pd.ExcelWriter("snf_stratified_summary.xlsx") as writer:
    summary_readmit.to_excel(writer, sheet_name="Readmitted", index=False)
    summary_no_readmit.to_excel(writer, sheet_name="Not_Readmitted", index=False)
    summary.to_excel(writer, sheet_name="Overall", index=False)

# Plot stratified results
plt.figure(figsize=(14, 6))

# Median LOS comparison
plt.subplot(1, 2, 1)
sns.barplot(data=summary_strat, x="risk_decile", y="median_los", hue="readmit_flag")
plt.title("Median LOS by Risk Decile (Stratified)")
plt.legend(title="Readmit", labels=["No", "Yes"])

# Boxplot stratified by readmit flag
plt.subplot(1, 2, 2)
sns.boxplot(data=df_clean, x="risk_decile", y="length_of_stay", hue="readmit_flag")
plt.title("LOS by Risk Decile and Readmit Status")
plt.legend(title="Readmit", labels=["No", "Yes"])

plt.tight_layout()
plt.savefig("snf_stratified_visuals.png", dpi=300)
plt.show()




