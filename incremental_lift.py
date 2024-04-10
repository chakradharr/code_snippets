# Assuming you have a dataset with features and a target variable (ppv) in a pandas DataFrame called "df"
# You want to test the incremental lift in ppv by adding one feature at a time

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score

# Load your dataset (replace with your actual data)
# df = pd.read_csv("your_data.csv")

# Define the target variable (ppv) and features
target = "ppv"
features = ["feature1", "feature2", "feature3", ...]  # Add your features here

# Split the data into train and test sets
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

# Initialize a dictionary to store incremental lift results
incremental_lift = {}

# Train a logistic regression model with each feature added incrementally
for feature in features:
    # Train the model with the current set of features
    X_train = train_df[features[:features.index(feature) + 1]]
    y_train = train_df[target]
    model = LogisticRegression()
    model.fit(X_train, y_train)

    # Make predictions on the test set
    X_test = test_df[features[:features.index(feature) + 1]]
    y_pred = model.predict(X_test)

    # Calculate precision (ppv) for the current model
    precision = precision_score(test_df[target], y_pred)

    # Calculate incremental lift compared to the previous model
    if len(incremental_lift) > 0:
        prev_precision = incremental_lift[list(incremental_lift.keys())[-1]]
        lift = precision - prev_precision
    else:
        lift = precision

    # Store the incremental lift
    incremental_lift[feature] = lift

# Print the incremental lift results
print("Incremental Lift in PPV:")
for feature, lift in incremental_lift.items():
    print(f"{feature}: {lift:.4f}")

