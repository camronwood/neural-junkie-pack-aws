"""AWS Organizations multi-account traversal."""
from __future__ import annotations

from aws_common import allowed_accounts, client, dry_run_enabled, dry_run_payload, profile_name


def list_organization_accounts(body: dict, settings: dict, pack_dir: str) -> dict:
    tool = "list_organization_accounts"
    if dry_run_enabled(settings):
        return {
            **dry_run_payload(tool, body),
            "items": [
                {"id": "123456789012", "name": "prod", "email": "ops@example.com", "status": "ACTIVE"},
                {"id": "210987654321", "name": "dev", "email": "dev@example.com", "status": "ACTIVE"},
            ],
        }
    org = client(settings, "organizations")
    allow = allowed_accounts(settings)
    items = []
    token = body.get("next_token")
    while True:
        params = {}
        if token:
            params["NextToken"] = str(token)
        resp = org.list_accounts(**params)
        for acct in resp.get("Accounts", []):
            acct_id = acct.get("Id", "")
            if allow and acct_id not in allow:
                continue
            items.append(
                {
                    "id": acct_id,
                    "name": acct.get("Name"),
                    "email": acct.get("Email"),
                    "status": acct.get("Status"),
                }
            )
        token = resp.get("NextToken")
        if not token:
            break
    return {"items": items, "count": len(items), "next_token": None}


def assume_account_context(body: dict, settings: dict, pack_dir: str) -> dict:
    tool = "assume_account_context"
    account_id = str(body.get("account_id", "") or "").strip()
    if not account_id:
        raise ValueError("missing required parameter: account_id")
    if dry_run_enabled(settings):
        return {
            **dry_run_payload(tool, body),
            "account_id": account_id,
            "profile": profile_name(settings),
            "ready": True,
        }
    org = client(settings, "organizations")
    resp = org.list_accounts()
    match = next((a for a in resp.get("Accounts", []) if a.get("Id") == account_id), None)
    if not match:
        raise ValueError(f"account {account_id} not found in organization")
    return {
        "account_id": account_id,
        "account_name": match.get("Name"),
        "profile": profile_name(settings),
        "message": "Use active SSO profile; cross-account role assumption is configured via your AWS profile chain.",
        "ready": True,
    }
