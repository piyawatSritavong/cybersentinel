# Standard Operating Procedure: High Severity Alerts

## 1. Overview
High severity alerts represent critical security incidents with a high likelihood of immediate impact to the organization. These require immediate escalation and response.

## 2. Examples
- Confirmed SQL Injection (SQLi) or Remote Code Execution (RCE) on a public-facing server.
- Ransomware activity detected (e.g., mass file encryption, volume shadow copy deletion).
- Data exfiltration to known malicious command-and-control (C2) servers.

## 3. Investigation Steps
1. **IMMEDIATE CONTAINMENT:** Isolate the affected system from the network immediately.
2. Determine the scope of the compromise (what data or systems were accessed).
3. Identify the initial attack vector (e.g., phishing email, vulnerable service).
4. Preserve evidence for forensic analysis.
5. Escalate to the Incident Response (IR) team and notify stakeholders.

## 4. Remediation & Action (ISO 27001 / NIST Aligned)
- **Containment:** Block malicious IPs, disable compromised accounts, isolate hosts.
- **Eradication:** Remove malicious artifacts, patch vulnerabilities, rebuild systems from clean backups if necessary.
- **Recovery:** Restore services, monitor for reinfection.
- **Post-Incident:** Conduct a post-mortem review to improve defenses.
