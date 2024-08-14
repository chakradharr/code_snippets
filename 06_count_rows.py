import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

# Initialize BigQuery client
credentials = service_account.Credentials.from_service_account_file('path/to/your/service-account-key.json')
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

# Define your table names
tables = [
    "your_project.your_dataset.table_1",
    "your_project.your_dataset.table_2",
    "your_project.your_dataset.table_3"
    # Add more tables as needed
]

# Initialize an empty list to store the results
data = []

# Function to get count of rows, distinct member_id, and distinct service_auth_no
def get_table_stats(table_name):
    query = f"""
    SELECT
        COUNT(*) AS row_count,
        COUNT(DISTINCT member_id) AS distinct_member_id_count,
        COUNT(DISTINCT service_auth_no) AS distinct_service_auth_no_count
    FROM `{table_name}`
    """
    query_job = client.query(query)
    result = query_job.result().to_dataframe()
    
    result['table_name'] = table_name
    return result

# Iterate through each table and get the stats
for table in tables:
    stats = get_table_stats(table)
    data.append(stats)

# Combine all the results into a single DataFrame
df = pd.concat(data).reset_index(drop=True)
df = df[['table_name', 'row_count', 'distinct_member_id_count', 'distinct_service_auth_no_count']]

# Display the DataFrame
print(df)

# Optionally, save the DataFrame to a CSV file
df.to_csv("table_statistics.csv", index=False)