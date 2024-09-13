import pandas as pd
import json

# Function to transform the payload
def transform_payload(input_payload):
    data = json.loads(input_payload)
    
    # Create a new dictionary with the required structure
    transformed = {
        "ServiceAuth": {
            "EventControlID": data["ServiceAuth"].get("AccountTier2", ""),
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
            "SAUpdateon": data["ServiceAuth"].get("SAUpdateon", ""),
            "PrecertStatus": "PENGD",
            "PrecertStatusType": "A",
            "PrimaryAddress": data["ServiceAuth"].get("PrimaryAddress", ""),
            "CoverageStartDate": data["ServiceAuth"].get("CoverageStartDate", ""),
            "ProductType": data["ServiceAuth"].get("ProductType", ""),
            "ProductName": data["ServiceAuth"].get("ProductName", ""),
            "FundingSelfInsuredIndicator": data["ServiceAuth"].get("FundingSelfInsuredIndicator", ""),
            "Segment": "Group",
            "SubSegment": "INDVL",
            "AccountTierSubsegment": "100512",
            "PlatformCode": "HRP",
            "AccountTier1": "00001",
            "ActualAdmitDate": data["ServiceAuth"].get("ActualAdmitDate", ""),
            "ActualDischargeDate": data["ServiceAuth"].get("ActualDischargeDate", ""),
            "DischargeTo": data["ServiceAuth"].get("DischargeTo", ""),
            "CaseTypeCode": data["ServiceAuth"].get("CaseTypeCode", ""),
            "LOBCode": "200500",
            "StateOrRegion": "WI",
            "PrimaryCoverage": "TRUE",
            "ClassID": data["ServiceAuth"].get("ClassID", ""),
            "ServiceLineItem": data["ServiceAuth"].get("ServiceLineItem", []),
            "Diagnosis": data["ServiceAuth"].get("Diagnosis", [])
        }
    }
    
    # Convert the dictionary back to JSON string
    return json.dumps(transformed, indent=4)

# Example DataFrame
data = {
    'json_column': ['current_json_string_1', 'current_json_string_2']  # These should be actual JSON strings
}
df = pd.DataFrame(data)

# Apply the transformation function
df['transformed_json'] = df['json_column'].apply(transform_payload)

# Optionally, save the DataFrame to a CSV file
df.to_csv('transformed_payloads.csv', index=False)

# Show the result
print(df)