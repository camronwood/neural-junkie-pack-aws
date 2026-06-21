# Neural Junkie — AWS pack

Official domain pack for [Neural Junkie](https://github.com/camronwood/neural-junkie).

Adds **AWSExpert** with read-only AWS CLI MCP tools and SSO profile integration via **Settings → Integrations**.

Install via desktop **Settings → Domain packs → Pack store**, or sideload `dist/aws-<version>.zip`.

## Develop

```bash
make verify
make pack-zip   # dist/aws-<version>.zip
```

Tag `v1.0.0` and push to publish the release zip to GitHub.
