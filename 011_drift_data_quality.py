import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import ks_2samp

# Load your datasets
# Assuming train and prod data are pandas DataFrames
train_df = pd.read_csv('train_data.csv')  # Load your training data
prod_df = pd.read_csv('prod_data.csv')  # Load your production data

# Step 1: Check for Missing Values
def check_missing_data(df, df_name):
    missing = df.isnull().mean() * 100
    print(f"\nMissing Data Percentage in {df_name}:\n", missing[missing > 0])

print("Checking Missing Data")
check_missing_data(train_df, "Training Data")
check_missing_data(prod_df, "Production Data")

# Step 2: Compare Feature Distributions (Using Kolmogorov-Smirnov Test)
def compare_distributions(train, prod, feature):
    # KS Test to compare distribution
    statistic, p_value = ks_2samp(train[feature].dropna(), prod[feature].dropna())
    
    # Plot feature distributions
    plt.figure(figsize=(10, 6))
    sns.kdeplot(train[feature], label='Training', shade=True)
    sns.kdeplot(prod[feature], label='Production', shade=True)
    plt.title(f"Distribution Comparison for {feature}")
    plt.legend()
    plt.show()
    
    print(f"\nFeature: {feature}")
    print(f"KS Statistic: {statistic:.4f}, P-Value: {p_value:.4f}")
    if p_value < 0.05:
        print(f"Warning: The feature '{feature}' shows a significant difference between Training and Production data.\n")
    else:
        print(f"The feature '{feature}' does not show significant distribution changes.\n")

# Step 3: Check for Feature Drift
def check_feature_drift(train_df, prod_df):
    numerical_features = train_df.select_dtypes(include=[np.number]).columns.tolist()

    for feature in numerical_features:
        if feature in prod_df.columns:
            compare_distributions(train_df, prod_df, feature)

print("Checking Feature Drift")
check_feature_drift(train_df, prod_df)

# Step 4: Check for Categorical Feature Drift (Optional if you have categorical features)
def compare_categorical_distribution(train, prod, feature):
    train_dist = train[feature].value_counts(normalize=True)
    prod_dist = prod[feature].value_counts(normalize=True)
    
    comparison_df = pd.DataFrame({'Training': train_dist, 'Production': prod_dist}).fillna(0)
    comparison_df.plot(kind='bar', figsize=(10, 6), title=f'Categorical Distribution: {feature}')
    plt.show()

def check_categorical_drift(train_df, prod_df):
    categorical_features = train_df.select_dtypes(include=[object]).columns.tolist()
    
    for feature in categorical_features:
        if feature in prod_df.columns:
            compare_categorical_distribution(train_df, prod_df, feature)

print("Checking Categorical Drift")
check_categorical_drift(train_df, prod_df)

# Step 5: Check for New/Unknown Categories in Production Data
def check_new_categories(train_df, prod_df):
    categorical_features = train_df.select_dtypes(include=[object]).columns.tolist()
    
    for feature in categorical_features:
        if feature in prod_df.columns:
            new_categories = set(prod_df[feature].unique()) - set(train_df[feature].unique())
            if new_categories:
                print(f"New categories found in production data for feature '{feature}': {new_categories}")

print("Checking for New Categories in Categorical Features")
check_new_categories(train_df, prod_df)