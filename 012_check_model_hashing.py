import hashlib

# Function to compute the MD5 hash of a file
def hash_file(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

# Example usage: Calculate hash for the training and production models
train_model_filepath = 'path_to_training_model.pkl'  # Path to your saved training pickle file
prod_model_filepath = 'path_to_production_model.pkl'  # Path to your production pickle file

train_model_hash = hash_file(train_model_filepath)
prod_model_hash = hash_file(prod_model_filepath)

# Compare the hashes to see if the files are the same
if train_model_hash == prod_model_hash:
    print("The correct model version is deployed in production.")
else:
    print("Model version mismatch! The production model is different.")