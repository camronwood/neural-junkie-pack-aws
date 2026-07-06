# AWS workspace

Configure SSO profiles in **Settings → Integrations** before consulting AWSExpert.

## SSO setup

1. Ensure `~/.aws/config` has your SSO profiles (e.g. `AdministratorAccess-046456031965`).
2. Select the active profile and default region in Integrations.
3. Run `aws sso login --profile <profile>` in a terminal when your session expires.
4. Use **Test connection** to verify `sts get-caller-identity`.

## Sidecar setup

```bash
./scripts/setup-aws-sidecar.sh
```

The hub starts the boto3 sidecar when the AWS pack is enabled. Typed tools call `/api/aws/*` routes instead of free-form CLI passthrough.

## Read-only default

AWSExpert uses **read-only** typed tools by default. Mutating operations require:

- **Enable write operations** in Settings → Integrations
- Explicit user approval echoed as `confirm_token` on each write tool call
- Audit log at `~/.neural-junkie/aws-audit.log`

## Multi-account allowlists

Optional **allowed profiles** and **allowed accounts** restrict which SSO profiles and AWS account IDs the sidecar may query. Leave empty to allow the active profile only.

Use **List org accounts** in Integrations to verify Organizations access.

## Role boundaries

| Concern | Owner |
|---------|-------|
| Live EC2/S3/IAM/Lambda/alarms, SSO, Cost Explorer, Security Hub | **AWSExpert** |
| Repo CI/CD, GitHub Actions, K8s/Helm/Docker | **PlatformEngineer** |
| Terraform/CDK **authoring** in repo | **PlatformEngineer** |
| IaC **drift vs live account** | **AWSExpert** (consult PlatformEngineer for file changes) |
| Jira tickets, incident triage | **IncidentManager** |

See `assets/runbooks/aws-vs-platform-engineer.md` and `assets/runbooks/alarm-to-jira-handoff.md`.

## IAM permissions (optional lenses)

| Lens | IAM |
|------|-----|
| Core describe | `ec2:Describe*`, `s3:List*`, `lambda:Get*`, `lambda:List*`, `iam:Get*`, `cloudformation:Describe*` |
| Cost Explorer | `ce:GetCostAndUsage` |
| Security Hub | `securityhub:GetFindings` |
| GuardDuty | `guardduty:ListFindings`, `guardduty:GetFindings` |
| Organizations | `organizations:ListAccounts` |

Sidecar returns clear errors when APIs are denied.

## Pagination

List/describe tools accept optional `page_size` (default 20, max 100) and return `{ items, next_token }`.

## Collab with incident-management

For prod alarms: `@AWSExpert` traces the resource → `@IncidentManager` files Jira. Requires both AWS and Incident management packs enabled.

Runbook: `assets/runbooks/alarm-to-jira-handoff.md`.
