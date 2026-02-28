# Standard Operating Procedure: Low Severity Alerts

## 1. Overview
Low severity alerts typically represent authorized activities, misconfigurations, or noisy scanners that pose minimal immediate risk. 

## 2. Examples
- Authorized vulnerability scans (e.g., Nessus, Qualys) originating from known IP subnets.
- Single user login failures (under 3 attempts).
- Routine software updates triggering generic network alerts.

## 3. Investigation Steps
1. Verify the source IP against the known authorized scanners list.
2. Check if the activity coincides with approved maintenance windows.
3. Confirm no subsequent successful exploitation occurred.

## 4. Remediation & Action
- No immediate action required if verified as authorized.
- Suppress or tune the rule if it generates excessive noise.
- Close as False Positive (or True Positive - Expected Behavior).
