# Alarm → AWS trace → Jira handoff

Cross-pack runbook for **AWS** + **Incident management** packs.

## Prerequisites

- AWS pack enabled; SSO profile configured and logged in
- Incident management pack enabled; Jira credentials in Settings → Integrations

## Steps

1. **Triage** — `@IncidentManager` captures alarm name, time, severity, and environment.
2. **Trace** — `@AWSExpert`:
   - Identify resource from alarm dimensions (instance ID, Lambda name, etc.)
   - Call typed tools: `describe_ec2_instances`, `get_lambda_config`, or `describe_cloudformation_stack`
   - Summarize root cause hypothesis (config drift, capacity, dependency failure)
3. **Ticket** — `@IncidentManager`:
   - Create or update Jira issue with severity (P0–P4 per org rubric)
   - Include resource ARN/ID and AWSExpert summary in description
   - Add comment with next actions
4. **Fix path** — If code/CI change needed → `@PlatformEngineer`. If account config → AWSExpert (read-only) documents change; human applies or enables gated write.

## Severity guide

| Level | When |
|-------|------|
| P0 | Full prod outage, data loss risk |
| P1 | Major feature degraded, no workaround |
| P2 | Partial degradation, workaround exists |
| P3 | Minor impact, internal only |
| P4 | Cosmetic / low urgency |

## Collab scenario

Pack smoke fixture: `scenarios/collab/aws-alarm-incident-handoff.json`
