import pandas as pd
import numpy as np

# Creating sample data
data = {
    'pme_reference_no': ['PME001', 'PME002', 'PME003', 'PME004', 'PME005'],
    't': [1, 2, 3, 4, 5],
    'feature1': np.random.randint(0, 100, size=5),  # Random integers for feature1
    'feature2': np.random.randint(0, 100, size=5)   # Random integers for feature2
}

# Creating DataFrame
df = pd.DataFrame(data)

# Displaying the DataFrame
print(df)


import dask.dataframe as dd

def expand_dataset_dask(data, id_col='pme_reference_no', time_col='t', end_time=30):
    """
    A function that expands a dataset for each value of ID from its t value till t=30 and sorts it by ID and time using Dask.
    
    Parameters:
        data (dd.DataFrame): The original Dask DataFrame.
        id_col (str): The column name for ID (default: 'pme_reference_no').
        time_col (str): The column name for time (default: 't').
        end_time (int): The end time for expansion (default: 30).
        
    Returns:
        dd.DataFrame: The expanded and sorted Dask DataFrame.
    """
    
    def process_group(group):
        start_time = group[time_col].min().compute()
        time_range = pd.DataFrame({time_col: np.arange(start_time, end_time + 1)})
        time_range[id_col] = group[id_col].iloc[0].compute()
        expanded_group = pd.merge(time_range, group.compute(), on=[id_col, time_col], how='left')
        return expanded_group
    
    grouped = data.groupby(id_col)
    results = [process_group(group) for _, group in grouped]
    
    result = dd.from_pandas(pd.concat(results), npartitions=data.npartitions)
    
    return result

# Example usage:
# Assuming your Dask DataFrame is named test_ddf_tmp and contains columns 'pme_reference_no' and 't'
test_ddf_tmp = dd.from_pandas(test_df_tmp, npartitions=8)
expanded_ddf = expand_dataset_dask(test_ddf_tmp, id_col='pme_reference_no', time_col='t', end_time=30)

# Compute and display the result
expanded_df = expanded_ddf.compute()
print(expanded_df)


import pandas as pd
import numpy as np
from joblib import Parallel, delayed

def expand_dataset(data, id_col='pme_reference_no', time_col='t', end_time=30, n_jobs=-1):
    """
    A function that expands a dataset for each value of ID from its t value till t=30 and sorts it by ID and time.
    
    Parameters:
        data (pd.DataFrame): The original dataset.
        id_col (str): The column name for ID (default: 'pme_reference_no').
        time_col (str): The column name for time (default: 't').
        end_time (int): The end time for expansion (default: 30).
        n_jobs (int): The number of jobs for parallel processing (default: -1 for all available cores).
        
    Returns:
        pd.DataFrame: The expanded and sorted dataset.
    """
    
    # Ensure the data is sorted by ID and time
    data = data.sort_values(by=[id_col, time_col]).reset_index(drop=True)
    
    # Function to process each group
    def process_group(group):
        start_time = group[time_col].min()
        time_range = pd.DataFrame({time_col: np.arange(start_time, end_time + 1)})
        time_range[id_col] = group[id_col].iloc[0]
        
        # Merge with the original subset
        expanded_group = pd.merge(time_range, group, on=[id_col, time_col], how='left')
        return expanded_group
    
    # Group by ID and process in parallel
    grouped = data.groupby(id_col)
    results = Parallel(n_jobs=n_jobs)(delayed(process_group)(group) for _, group in grouped)
    
    # Concatenate results and sort
    result = pd.concat(results).sort_values(by=[id_col, time_col]).reset_index(drop=True)
    
    return result

# Example usage:
# Assuming your DataFrame is named test_df_tmp and contains columns 'pme_reference_no' and 't'
expanded_df = expand_dataset(test_df_tmp, id_col='pme_reference_no', time_col='t', end_time=30)

# Display the result
print(expanded_df)



import pandas as pd

def expand_dataset(data, id_col='pme_reference_no', time_col='t', end_time=30):
    """
    A function that expands a dataset for each value of ID from its t value till t=30 and sorts it by ID and time.
    
    Parameters:
        data (pd.DataFrame): The original dataset.
        id_col (str): The column name for ID (default: 'pme_reference_no').
        time_col (str): The column name for time (default: 't').
        end_time (int): The end time for expansion (default: 30).
        
    Returns:
        pd.DataFrame: The expanded and sorted dataset.
    """
    expanded_data = []
    
    unique_ids = data[id_col].unique()
    
    for uid in unique_ids:
        subset = data[data[id_col] == uid]
        if subset.empty:
            continue
        
        start_time = subset[time_col].min()
        time_range = pd.DataFrame({time_col: range(start_time, end_time + 1)})
        time_range[id_col] = uid
        
        merged_data = pd.merge(time_range, subset, on=[id_col, time_col], how='left')
        expanded_data.append(merged_data)
    
    result = pd.concat(expanded_data).sort_values(by=[id_col, time_col]).reset_index(drop=True)
    
    return result

# Example usage:
# Assuming your DataFrame is named test_df_tmp and contains columns 'pme_reference_no' and 't'
expanded_df = expand_dataset(test_df_tmp, id_col='pme_reference_no', time_col='t', end_time=30)

# Display the result
print(expanded_df)


import dask.dataframe as dd
import pandas as pd
import numpy as np

def expand_dataset_dask(data, id_col='pme_reference_no', time_col='t', end_time=30):
    """
    A function that expands a dataset for each value of ID from its t value till t=30 and sorts it by ID and time using Dask.
    
    Parameters:
    data (dd.DataFrame): The original Dask DataFrame.
    id_col (str): The column name for ID (default: 'pme_reference_no').
    time_col (str): The column name for time (default: 't').
    end_time (int): The end time for expansion (default: 30).

    Returns:
    dd.DataFrame: The expanded and sorted Dask DataFrame.
    """
    
    def process_group(group):
        start_time = group[time_col].min().compute()
        time_range = pd.DataFrame({time_col: np.arange(start_time, end_time + 1)})
        time_range[id_col] = group[id_col].iloc[0].compute()
        expanded_group = pd.merge(time_range, group.compute(), on=[id_col, time_col], how='left')
        return expanded_group

    grouped = data.groupby(id_col)
    results = grouped.apply(lambda group: process_group(group)).compute()
    result = dd.from_pandas(pd.concat(results), npartitions=data.npartitions)
    
    return result

# Assuming your Dask DataFrame is named test_dd and contains columns 'pme_reference_no' and 't'
test_dd = dd.from_pandas(test_df, npartitions=8)
expanded_dd = expand_dataset_dask(test_dd)
expanded_dd.compute()




