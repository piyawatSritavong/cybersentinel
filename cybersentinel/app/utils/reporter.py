from datetime import datetime

def generate_executive_report(verdict: str, alert_data: dict, reasoning: dict) -> str:
    """
    Generate an executive-level report summarizing the alert triage.
    """
    if verdict == "True Positive":
        recommendation = "Immediate action required - escalate to Tier 2"
    else:
        recommendation = "No action required - mark as False Positive"

    report = f"""
# Executive Report - Alert Triage

**Generated:** {datetime.utcnow().isoformat()}

## Summary
- **Verdict:** {verdict}
- **Alert ID:** {alert_data.get('alert_id', 'Unknown')}
- **Risk Score:** {alert_data.get('risk_score', 'N/A')}

## Details
{alert_data.get('description', 'No description available')}

## Analysis
- **Analyst Assessment:** {reasoning.get('analyst', 'N/A')}
- **Skeptic Review:** {reasoning.get('skeptic', 'N/A')}
- **Final Judgment:** {reasoning.get('judge', 'N/A')}

## Recommendation
{recommendation}
"""
    return report

def generate_technical_report(verdict: str, alert_data: dict, reasoning: dict, playbook_refs: list) -> str:
    """
    Generate a detailed technical report for SOC analysts.
    """
    if verdict == "True Positive":
        next_steps = "1. Escalate to Tier 2 analyst\n2. Investigate source IP/user\n3. Check for lateral movement"
    else:
        next_steps = "1. Mark as False Positive\n2. Update detection rules if necessary"
        
    playbooks_str = chr(10).join([f"- {ref}" for ref in playbook_refs]) if playbook_refs else "No playbook references found"

    report = f"""
# Technical Report - Alert Triage

**Generated:** {datetime.utcnow().isoformat()}

## Alert Information
- **Alert ID:** {alert_data.get('alert_id', 'Unknown')}
- **Source:** {alert_data.get('source', 'Unknown')}
- **Timestamp:** {alert_data.get('timestamp', 'Unknown')}
- **Risk Score:** {alert_data.get('risk_score', 'N/A')}

## Raw Data (Masked)
```
{alert_data.get('raw_data', 'No raw data available')}
```

## Multi-Agent Analysis

### Analyst Agent (DeepSeek-R1)
{reasoning.get('analyst', 'No analysis available')}

### Skeptic Agent (Llama 3.3)
{reasoning.get('skeptic', 'No skeptic review available')}

### Log Correlation
{reasoning.get('correlation', 'No correlation analysis available')}

### Judge Agent (Final Verdict)
{reasoning.get('judge', 'No final judgment available')}

## Playbook References
{playbooks_str}

## Verdict
**{verdict}**

## Recommended Remediation (ISO 27001 / NIST)
{reasoning.get('remediation', 'N/A')}

## Next Steps
{next_steps}
"""
    return report
