import numpy as np
import pandas as pd

def compute_cdf_from_dataframe(df):
    cdf_values = []
    unique_ids = df['ID'].unique()
    for id_ in unique_ids:
        group_df = df[df['ID'] == id_]
        hazard_probabilities = group_df['hazard_prob']
        cdf = np.zeros(len(hazard_probabilities))
        for t in range(len(hazard_probabilities)):
            cdf[t] = np.sum(hazard_probabilities[t:])  # CDF at time t = sum of probabilities from t to 30
        cdf_values.extend(cdf)
    return cdf_values

# Example usage:
# Assuming your dataframe is named 'df' and contains columns 'ID' and 'hazard_prob'
# Call the function passing the dataframe as input
cdf_values = compute_cdf_from_dataframe(df)

# Add the computed CDF values to the dataframe
df['cdf'] = cdf_values

# Display the updated dataframe
print(df)
