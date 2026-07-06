# Security review (read-only)

1. **Security Hub** — `list_security_hub_findings` filtered by `severity` (CRITICAL/HIGH first).
2. **GuardDuty** — `list_guardduty_findings` in the alarm region.
3. **IAM** — `analyze_iam_policy` for suspect roles; `describe_iam_role` for trust policies.
4. Escalate mutating remediations to human approval; enable write mode only for approved break-glass actions.

Pair with `@SecurityReviewer` (SD pack) for application-layer findings.
