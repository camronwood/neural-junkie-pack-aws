# AWSExpert vs PlatformEngineer

Use this runbook when both the **AWS** and **Software development** packs are enabled.

## Ownership matrix

| Concern | AWSExpert | PlatformEngineer |
|---------|-----------|-------------------|
| Live account state (EC2, S3, IAM, Lambda, CloudWatch alarms) | **Owns** | Defer `@AWSExpert` |
| Repo CI/CD (GitHub Actions, Jenkins, release pipelines) | Defer `@PlatformEngineer` | **Owns** |
| K8s / Helm / Docker manifests in repo | Defer `@PlatformEngineer` | **Owns** |
| Terraform / CDK / CloudFormation **files in repo** | Consult for drift / live state | **Owns** authoring |
| SSO profiles, Organizations, Cost Explorer, Security Hub | **Owns** | Defer `@AWSExpert` |
| `terraform apply` / CDK deploy | **Never** (human + PlatformEngineer workflow) | **Owns** repo-side changes |

## Consult triggers

- Live AWS question → `@AWSExpert`
- Pipeline / k8s / docker question → `@PlatformEngineer`
- Alarm in prod → `@AWSExpert` investigate, then `@IncidentManager` if ticketing needed

## Avoid overlap

- PlatformEngineer should **not** run `kubectl` or AWS describe tools when the task is account investigation — defer to AWSExpert.
- AWSExpert should **not** edit `.github/workflows`, Helm charts, or Dockerfiles unless explicitly assigned — defer to PlatformEngineer.
