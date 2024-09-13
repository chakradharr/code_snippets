import pandas as pd
import json

# Function to transform the payload based on new mappings
def transform_payload(input_payload):
    data = json.loads(input_payload)
    
    # Create a new dictionary with the required structure, directly mapping old fields to new ones
    transformed = {
        "ServiceAuth": {
            "EventControlID": data["ServiceAuth"].get("AuthorizationId", ""),
            "BatchControlID": data["ServiceAuth"].get("AccountId1", ""),
            "EventRequestDTS": data["ServiceAuth"].get("EventLoggedDTS", ""),
            "EventRequestType": "UM Event",
            "RPARequestType": data["ServiceAuth"].get("AuthorizationId", ""),
            "ApplicationId": data["ServiceAuth"].get("ApplicationId", ""),
            "MemberIdSource": data["ServiceAuth"].get("MemberIdSource", ""),
            "MemberIdValue": data["ServiceAuth"].get("MemberIdValue", ""),
            "PayorId": data["ServiceAuth"].get("PayorId", ""),
            "MemberDOB": data["ServiceAuth"].get("MemberDOB", ""),
            "GenderTypeKey": data["ServiceAuth"].get("GenderTypeKey", ""),
            "AuthorizationID": data["ServiceAuth"].get("AuthorizationId", ""),
            "SAUpdateon": data["ServiceAuth"].get("SAUpdatedon", ""),
            "PrecertStatus": data["ServiceAuth"].get("PrecertStatus", ""),
            "PrecertStatusType": data["ServiceAuth"].get("PrecertStatusType", ""),
            "PrimaryAddress": data["ServiceAuth"].get("PrimaryAddress", ""),
            "CoverageStartDate": data["ServiceAuth"].get("CoverageStartDate", ""),
            "ProductType": data["ServiceAuth"].get("ProductType", ""),
            "ProductName": data["ServiceAuth"].get("ProductName", ""),
            "FundingSelfInsuredIndicator": data["ServiceAuth"].get("FundingSelfInsuredIndicator", ""),
            "Segment": data["ServiceAuth"].get("Segment", ""),
            "SubSegment": data["ServiceAuth"].get("SubSegment", ""),
            "AccountTierSubsegment": data["ServiceAuth"].get("AccountTierSubsegment", ""),
            "PlatformCode": data["ServiceAuth"].get("PlatformCode", ""),
            "AccountTier1": data["ServiceAuth"].get("AccountTier1", ""),
            "ActualAdmitDate": data["ServiceAuth"].get("ActualAdmitDate", ""),
            "ActualDischargeDate": data["ServiceAuth"].get("ActualDischargeDate", ""),
            "DischargeTo": data["ServiceAuth"].get("DischargeTo", ""),
            "CaseTypeCode": data["ServiceAuth"].get("CaseTypeCode", ""),
            "LOBCode": data["ServiceAuth"].get("LOBCode", ""),
            "StateOrRegion": data["ServiceAuth"].get("StateOrRegion", ""),
            "PrimaryCoverage": data["ServiceAuth"].get("PrimaryCoverage", ""),
            "ClassID": data["ServiceAuth"].get("ClassID", ""),
            "ServiceLineItem": data["ServiceAuth"].get("ServiceLineItem", []),
            "Diagnosis": data["ServiceAuth"].get("Diagnosis", [])
        }
    }
    
    # Convert the dictionary back to JSON string
    return json.dumps(transformed, indent=4)

# Example DataFrame with JSON strings in one column
data = {
    'json_column': ['current_json_string_1', 'current_json_string_2']  # Replace with actual JSON strings
}
df = pd.DataFrame(data)

# Apply the transformation function
df['transformed_json'] = df['json_column'].apply(transform_payload)

# Optionally, save the DataFrame to a CSV file
df.to_csv('transformed_payloads.csv', index=False)

# Print the DataFrame to check the transformed payloads
print(df)