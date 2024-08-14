from google.cloud import bigquery
from google.oauth2 import service_account

# Initialize BigQuery client
credentials = service_account.Credentials.from_service_account_file('path/to/your/service-account-key.json')
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

# Define your table names, identifiers, and the specific admit date
base_table = "your_project.your_dataset.base_table"
subsequent_tables = [
    "your_project.your_dataset.table_step_1",
    "your_project.your_dataset.table_step_2",
    # Add more tables as needed
]
identifiers = ["individual_id", "proxy_id"]  # List of identifiers to check in order of priority
admit_date = '2024-08-01'  # Replace with the actual admit date you are interested in

# Function to count records with a specific admit_date in a table for a specific identifier
def count_records_by_date(base_table, table, identifier, admit_date):
    query = f"""
    SELECT COUNT({identifier}) as count
    FROM `{table}`
    WHERE {identifier} IN (
        SELECT {identifier} 
        FROM `{base_table}` 
        WHERE admit_date = '{admit_date}' AND {identifier} IS NOT NULL
    )
    """
    query_job = client.query(query)
    result = query_job.result()
    return list(result)[0]['count']

# Get the count of records in the base table for each identifier
base_counts = {}
for identifier in identifiers:
    base_query = f"""
    SELECT COUNT({identifier}) as count
    FROM `{base_table}`
    WHERE admit_date = '{admit_date}' AND {identifier} IS NOT NULL
    """
    base_query_job = client.query(base_query)
    base_result = base_query_job.result()
    base_counts[identifier] = list(base_result)[0]['count']

# Iterate through each subsequent table and count how many records were dropped
for table in subsequent_tables:
    print(f"\nChecking table: {table}")
    
    for identifier in identifiers:
        count_in_table = count_records_by_date(base_table, table, identifier, admit_date)
        records_dropped = base_counts[identifier] - count_in_table
        
        print(f"{identifier}: {count_in_table} records found, {records_dropped} records dropped.")

# Example: Output the summary into a CSV file
import csv

with open("dropped_records_by_date.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["table", "identifier", "records_in_base", "records_in_table", "records_dropped"])
    
    for table in subsequent_tables:
        for identifier in identifiers:
            count_in_table = count_records_by_date(base_table, table, identifier, admit_date)
            records_dropped = base_counts[identifier] - count_in_table
            writer.writerow([table, identifier, base_counts[identifier], count_in_table, records_dropped])

print("Summary of dropped records has been saved to dropped_records_by_date.csv")