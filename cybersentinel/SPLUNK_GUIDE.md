# Splunk Integration Guide for CyberSentinel

This guide explains how to set up Splunk to send security alerts to CyberSentinel's `/v1/ingest` endpoint using a Webhook Alert Action.

## Prerequisites
1. CyberSentinel must be running and accessible from the Splunk server.
2. You must have your `APP_API_KEY` ready (defined in your `.env` file).

## Step 1: Create a Splunk Alert
1. In Splunk, run your desired security search query (e.g., failed logins, malware detections).
2. Click **Save As** -> **Alert**.
3. Configure the alert schedule and trigger conditions as appropriate for your use case.

## Step 2: Configure the Webhook Action
1. Under **Trigger Actions**, click **+ Add Actions** and select **Webhook**.
2. Set the **URL** to point to your CyberSentinel instance:
   `http://<cybersentinel-ip>:8000/v1/ingest`

## Step 3: Configure Headers and Payload
Unfortunately, standard Splunk Webhooks do not natively support setting custom HTTP headers (like `X-API-Key`) directly in the UI without a custom webhook add-on or a script.

### Option A: Using a Custom Alert Script (Recommended for Security)
Instead of the built-in webhook, use a script to send the payload with the required header.

1. Create a script (e.g., `send_to_cybersentinel.py`) on your Splunk Search Head:
```python
import sys
import json
import requests
import gzip

# Splunk passes the payload path as the 8th argument
payload_file = sys.argv[8]

with gzip.open(payload_file, 'rt') as f:
    payload = json.load(f)

# Extract relevant fields for CyberSentinel
data = {
    "alert_id": payload.get("sid", "unknown"),
    "description": payload.get("search_name", "Splunk Alert"),
    "raw_data": json.dumps(payload.get("result", {})),
    "source": "splunk",
    "risk_score": 50 # Default or extract if available
}

headers = {
    "X-API-Key": "YOUR_APP_API_KEY_HERE",
    "Content-Type": "application/json"
}

response = requests.post("http://<cybersentinel-ip>:8000/v1/ingest", json=data, headers=headers)
```
2. Configure the Splunk Alert Action to trigger this script.

### Option B: Modifying CyberSentinel (Alternative)
If you cannot use a script, you can pass the API key as a query parameter in the webhook URL (less secure):
`http://<cybersentinel-ip>:8000/v1/ingest?api_key=YOUR_APP_API_KEY_HERE`

*Note: This requires modifying `app/core/security.py` in CyberSentinel to accept the API key via query parameters in addition to headers.*

## Expected Response
When Splunk triggers the alert, CyberSentinel will process the log, mask PII, correlate it against past incidents, and return a JSON response summarizing the analysis and risk level, which can be logged back into Splunk if configured.
