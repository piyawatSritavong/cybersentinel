import re
import logging

def mask_pii(text: str) -> str:
    """
    Masks IP addresses, internal emails, and employee IDs from logs.
    """
    if not text:
        return text
        
    # Mask IPv4 addresses
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    text = re.sub(ip_pattern, '[REDACTED_IP]', text)
    
    # Mask Email addresses
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    text = re.sub(email_pattern, '[REDACTED_EMAIL]', text)
    
    # Mask Employee IDs (assuming format like EMP12345 or similar 5-6 digit numbers)
    emp_pattern = r'\bEMP\d{4,6}\b'
    text = re.sub(emp_pattern, '[REDACTED_EMP_ID]', text)
    
    return text
