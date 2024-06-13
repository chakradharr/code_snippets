from google.cloud import bigquery
import os

# Initialize a BigQuery client
client = bigquery.Client()

# Path to the directory containing your SQL files
sql_files_path = '/path/to/sql/files/'

# Get a list of all SQL files in the directory
sql_files = [f for f in os.listdir(sql_files_path) if f.endswith('.sql')]

# Execute each SQL file
for sql_file in sql_files:
    with open(os.path.join(sql_files_path, sql_file), 'r') as file:
        original_query = file.read()

    # Extract the file name without extension
    file_name = os.path.splitext(sql_file)[0]

    # Add CREATE OR REPLACE statement with the table name as the file name
    create_or_replace_statement = f"CREATE OR REPLACE TABLE your_dataset.{file_name} AS\n"
    modified_query = create_or_replace_statement + original_query

    # Execute the modified query
    query_job = client.query(modified_query)  # API request
    query_job.result()  # Waits for the query to finish

    print(f"Executed {sql_file} successfully.")