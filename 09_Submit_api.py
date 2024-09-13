import pandas as pd
import json
import requests

def transform_payload(input_payload):
    data = json.loads(input_payload)
    transformed = {
        "ServiceAuth": {
            # Map keys from the original payload to the new structure as required
            "EventControlID": data["ServiceAuth"].get("AuthorizationId", ""),
            # Add additional fields mapping as necessary
        }
    }
    return json.dumps(transformed)

def send_payload_to_api(json_payload, api_url):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(api_url, data=json_payload, headers=headers)
    return response

# Example DataFrame with JSON strings
data = {'json_column': ['json_string_1', 'json_string_2']}  # Replace with actual JSON strings
df = pd.DataFrame(data)

# Apply transformation and send payloads
api_url = 'https://yourapi.com/endpoint'  # Replace with the actual API endpoint URL
df['transformed_json'] = df['json_column'].apply(transform_payload)
df['api_response'] = df['transformed_json'].apply(lambda x: send_payload_to_api(x, api_url))

# Print the API responses to see results
print(df['api_response'].apply(lambda x: x.text))  # You might want to handle responses differently based on your needs

# Optionally, you can save the DataFrame if needed
df.to_csv('api_responses.csv', index=False)