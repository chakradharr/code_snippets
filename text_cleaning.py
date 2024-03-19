import re

def remove_phone_numbers_timestamps_and_timezones(input_string):
    # Remove phone numbers (formats: ###-###-####, (###) ###-####, 1-###-###-####, +1 ###-###-####)
    phone_number_pattern = r'((1-\d{3}-\d{3}-\d{4})|(\(\d{3}\) \d{3}-\d{4})|(\d{3}-\d{3}-\d{4})|(\+\d{1,2} \d{3}-\d{3}-\d{4}))'
    cleaned_string = re.sub(phone_number_pattern, '', input_string)

    # Remove timestamps (HH:MM:SS format)
    timestamp_pattern = r'\d{2}:\d{2}:\d{2}'
    cleaned_string = re.sub(timestamp_pattern, '', cleaned_string)

    # Remove time zone abbreviations (e.g., EST, CST, PST)
    timezone_pattern = r'\b(?:EST|CST|PST|Eastern Time|Central Time|Pacific Time)\b'
    cleaned_string = re.sub(timezone_pattern, '', cleaned_string, flags=re.IGNORECASE)

    return cleaned_string

# Example usage:
input_text = "My number is 212-555-1212, and the timestamp is 10:30:45. Also, CST is Central Standard Time."
cleaned_text = remove_phone_numbers_timestamps_and_timezones(input_text)
print("Cleaned text:", cleaned_text)



import re

def remove_dates(input_string):
    # Remove dates in formats like "Mar 30 2013", "2021-09-30", "9/23/2022", and "12/14/2022"
    date_pattern = r'\b(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b'
    cleaned_string = re.sub(date_pattern, '', input_string)

    return cleaned_string

# Example usage:
input_text = "Good Mar 30 2013 day! Also, 2021-09-30, 9/23/2022, and 12/14/2022 are other dates."
cleaned_text = remove_dates(input_text)
print("Cleaned text:", cleaned_text)
