# AWS workspace

Configure SSO profiles in **Settings → Integrations** before consulting AWSExpert.

1. Ensure `~/.aws/config` has your SSO profiles (e.g. `AdministratorAccess-046456031965`).
2. Select the active profile and default region in Integrations.
3. Run `aws sso login --profile <profile>` in a terminal when your session expires.
4. Use **Test connection** to verify `sts get-caller-identity`.

AWSExpert uses read-only CLI tools by default (describe/list/get operations only).
