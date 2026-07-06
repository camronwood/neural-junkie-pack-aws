# Neural Junkie — AWS pack

Official domain pack for [Neural Junkie](https://github.com/camronwood/neural-junkie).

Adds **AWSExpert** — account-aware SRE copilot with typed boto3 sidecar tools, IaC drift, cost/security lenses, multi-account allowlists, and gated writes.

Install via desktop **Settings → Domain packs → Pack store**, or sideload `dist/aws-<version>.zip`.

## Setup

```bash
make setup    # boto3 venv at ~/.neural-junkie/aws/venv
```

Configure SSO in **Settings → Integrations**, then enable the AWS pack.

## Develop

```bash
make verify       # manifest + sidecar smoke + zip build
make pack-smoke   # sidecar dry-run smoke only
make pack-zip     # dist/aws-<version>.zip
```

Scenarios: `scenarios/implement/` and `scenarios/collab/` (run via hub `scripts/pack-smoke.sh` or `--pack-dir`).

Tag `v2.0.0` and push to publish the release zip to GitHub.
