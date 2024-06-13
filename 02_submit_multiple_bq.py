from google.cloud import bigquery
import os

# Initialize a BigQuery client
client = bigquery.Client()

# Path to the directory containing your SQL files
sql_files_directory = 'path_to_your_sql_files_directory'

# New folder to save the modified SQL files
new_folder_name = 'modified_sql_files'
new_folder_path = os.path.join(sql_files_directory, new_folder_name)
os.makedirs(new_folder_path, exist_ok=True)

# List all SQL files in the directory
sql_files = [f for f in os.listdir(sql_files_directory) if f.endswith('.sql')]

# Define the mapping of old table names to new table names
table_name_mapping = {
    'old_table_name1': 'new_table_name1',
    'old_table_name2': 'new_table_name2',
    # Add more mappings as needed
}

# Track success and failure
success_files = []
failure_files = []

for sql_file in sql_files:
    file_path = os.path.join(sql_files_directory, sql_file)
    
    # Extract the table name from the file name (excluding the .sql extension)
    table_name = os.path.splitext(sql_file)[0]
    
    # Read the content of the SQL file
    with open(file_path, 'r') as file:
        query = file.read()
    
    # Replace each old table name with the new table name
    for old_name, new_name in table_name_mapping.items():
        query = query.replace(old_name, new_name)
    
    # Append CREATE TABLE statement at the beginning of the query
    create_table_statement = f"CREATE TABLE {table_name} AS\n"
    modified_query = create_table_statement + query
    
    # Save the modified query to the new folder
    new_file_path = os.path.join(new_folder_path, sql_file)
    with open(new_file_path, 'w') as new_file:
        new_file.write(modified_query)
    
    try:
        # Execute the query
        query_job = client.query(modified_query)
        
        # Wait for the job to complete
        result = query_job.result()
        
        print(f"Executed {sql_file} successfully with table name '{table_name}'")
        success_files.append(sql_file)
    except Exception as e:
        print(f"Failed to execute {sql_file}: {e}")
        failure_files.append(sql_file)

print("Execution Summary:")
print(f"Success: {success_files}")
print(f"Failure: {failure_files}")