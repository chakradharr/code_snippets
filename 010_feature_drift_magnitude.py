import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import ks_2samp
from scipy.spatial.distance import jensenshannon
from scipy.stats import wasserstein_distance
import xgboost as xgb

# Assuming your XGBoost model and datasets are loaded
# xgb_model is your trained XGBoost model
# train_df is the training dataset
# prod_df is the production dataset

# 1. Extract Feature Importance from XGBoost
def get_xgboost_feature_importance(model):
    importance = model.get_booster().get_score(importance_type='gain')
    importance_df = pd.DataFrame(list(importance.items()), columns=['Feature', 'Gain'])
    importance_df = importance_df.sort_values(by='Gain', ascending=False)
    return importance_df

# Get XGBoost feature importance
importance_df = get_xgboost_feature_importance(xgb_model)
print("Feature Importance based on Gain:")
print(importance_df)

# 2. Quantify Drift for Numerical Features
def compare_numerical_feature_drift(train_df, prod_df, feature):
    train_data = train_df[feature].dropna()
    prod_data = prod_df[feature].dropna()

    # Calculate Wasserstein distance (for numerical feature drift)
    drift_wasserstein = wasserstein_distance(train_data, prod_data)

    # KS Test (alternative method to check drift)
    ks_stat, p_value = ks_2samp(train_data, prod_data)
    
    return drift_wasserstein, ks_stat, p_value

# 3. Quantify Drift for Categorical Features
def compare_categorical_feature_drift(train_df, prod_df, feature):
    train_dist = train_df[feature].value_counts(normalize=True)
    prod_dist = prod_df[feature].value_counts(normalize=True)

    # Jensen-Shannon divergence for categorical feature drift
    js_divergence = jensenshannon(train_dist, prod_dist)

    return js_divergence

# 4. Combine Feature Importance with Drift Magnitude
def feature_drift_analysis(train_df, prod_df, model, numerical_features, categorical_features):
    importance_df = get_xgboost_feature_importance(model)
    
    drift_magnitude = []

    for feature in numerical_features:
        if feature in prod_df.columns:
            wasserstein_dist, ks_stat, p_value = compare_numerical_feature_drift(train_df, prod_df, feature)
            drift_magnitude.append({
                'Feature': feature,
                'Drift_Wasserstein': wasserstein_dist,
                'KS_Statistic': ks_stat,
                'P_Value': p_value
            })
    
    for feature in categorical_features:
        if feature in prod_df.columns:
            js_divergence = compare_categorical_feature_drift(train_df, prod_df, feature)
            drift_magnitude.append({
                'Feature': feature,
                'Drift_JS_Divergence': js_divergence
            })
    
    drift_df = pd.DataFrame(drift_magnitude)
    
    # Merge Feature Importance and Drift Magnitude
    result_df = pd.merge(importance_df, drift_df, on='Feature', how='inner')
    
    return result_df

# 5. Example Usage
numerical_features = train_df.select_dtypes(include=[np.number]).columns.tolist()
categorical_features = train_df.select_dtypes(include=[object]).columns.tolist()

# Perform the analysis
result_df = feature_drift_analysis(train_df, prod_df, xgb_model, numerical_features, categorical_features)
print(result_df)

# 6. Plot Feature Importance vs Drift (Optional)
plt.figure(figsize=(10, 6))
sns.scatterplot(x='Gain', y='Drift_Wasserstein', data=result_df, hue='Feature', s=100)
plt.title('Feature Importance (Gain) vs Drift Magnitude (Wasserstein Distance)')
plt.xlabel('Feature Importance (Gain)')
plt.ylabel('Drift Magnitude (Wasserstein Distance)')
plt.legend(loc='best')
plt.show()