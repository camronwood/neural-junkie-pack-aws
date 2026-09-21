# Neural Junkie — AWS pack

Official domain pack for [Neural Junkie](https://github.com/camronwood/neural-junkie).

Adds **AWSExpert** — account-aware SRE copilot with typed boto3 sidecar tools, IaC drift, cost/security lenses, multi-account allowlists, and gated writes. Pack-owned MCP catalog: `assets/mcp/tools.json` + hub `POST /mcp/call`.

Install via desktop **Settings → Domain packs → Pack store**, or sideload `dist/aws-<version>.zip`.

## Setup

```
make setup    # boto3 venv at ~/.neural-junkie/aws/venv
```

Configure SSO in **Settings → Integrations**, then enable the AWS pack.

## Develop

```
make verify       # manifest + sidecar smoke + zip build
make pack-smoke   # sidecar dry-run smoke only
make pack-zip     # dist/aws-2.1.0.zip
```

Scenarios: `scenarios/implement/` and `scenarios/collab/` (run via hub `scripts/pack-smoke.sh` or `--pack-dir`).

Tag `v2.1.0` and push to publish the release zip to GitHub.
