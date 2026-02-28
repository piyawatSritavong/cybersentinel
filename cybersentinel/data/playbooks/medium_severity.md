# Standard Operating Procedure: Medium Severity Alerts

## 1. Overview
Medium severity alerts indicate suspicious activities that could potentially lead to a compromise if left unaddressed. They require timely investigation.

## 2. Examples
- Multiple failed login attempts (Brute Force) from a single IP.
- Unusual lateral movement or scanning from an internal workstation.
- Antivirus detecting and blocking malware on an endpoint.

## 3. Investigation Steps
1. Identify the targeted user or system.
2. Check for successful logins following the failed attempts.
3. Review endpoint logs for any signs of malware execution or persistence.
4. Check if the user was traveling or using a VPN.

## 4. Remediation & Action
- If brute force is ongoing, block the source IP at the firewall.
- If an account was compromised, force a password reset and revoke active sessions.
- Isolate the endpoint if malware was not fully remediated by the AV.
- Document findings and close as True Positive if action was taken.
