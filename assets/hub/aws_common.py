"""Shared AWS sidecar helpers: sessions, pagination, guardrails, audit."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any


def _truthy(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    return str(val).strip().lower() not in ("0", "false", "no", "")


def _setting(settings: dict, *keys: str, default: str = "") -> str:
    for key in keys:
        val = settings.get(key)
        if val is not None and str(val).strip() != "":
            return str(val).strip()
    return default


def _list_setting(settings: dict, *keys: str) -> list[str]:
    raw = _setting(settings, *keys)
    if not raw:
        val = None
        for key in keys:
            if key in settings and settings[key] is not None:
                val = settings[key]
                break
        if isinstance(val, list):
            return [str(v).strip() for v in val if str(v).strip()]
        return []
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except json.JSONDecodeError:
            pass
    return [p.strip() for p in raw.split(",") if p.strip()]


def dry_run_enabled(settings: dict) -> bool:
    return _truthy(settings.get("aws_dry_run")) or _truthy(os.environ.get("NJ_AWS_DRY_RUN"))


def read_only_enabled(settings: dict) -> bool:
    if "aws_read_only" in settings:
        return _truthy(settings.get("aws_read_only"))
    if "read_only" in settings:
        return _truthy(settings.get("read_only"))
    return True


def write_enabled(settings: dict) -> bool:
    return _truthy(settings.get("aws_write_enabled"))


def profile_name(settings: dict) -> str:
    return _setting(settings, "aws_profile", "profile")


def region_name(settings: dict) -> str:
    return _setting(settings, "aws_default_region", "default_region", default="us-east-2")


def allowed_profiles(settings: dict) -> list[str]:
    return _list_setting(settings, "aws_allowed_profiles", "allowed_profiles")


def allowed_accounts(settings: dict) -> list[str]:
    return _list_setting(settings, "aws_allowed_accounts", "allowed_accounts")


def audit_log_path(settings: dict) -> str:
    path = _setting(
        settings,
        "aws_write_audit_path",
        "write_audit_path",
        default="~/.neural-junkie/aws-audit.log",
    )
    return os.path.expanduser(path)


def profile_allowed(settings: dict, profile: str) -> bool:
    profile = profile.strip()
    if not profile:
        return False
    allowed = allowed_profiles(settings)
    if not allowed:
        return True
    return profile in allowed


def account_allowed(settings: dict, account_id: str) -> bool:
    account_id = str(account_id).strip()
    if not account_id:
        return True
    allowed = allowed_accounts(settings)
    if not allowed:
        return True
    return account_id in allowed


def clamp_page_size(raw: Any, default: int = 20, maximum: int = 100) -> int:
    try:
        size = int(raw)
    except (TypeError, ValueError):
        size = default
    if size < 1:
        size = default
    return min(size, maximum)


def paginate_result(items: list[Any], page_size: int, next_token: str | None = None) -> dict:
    start = 0
    if next_token:
        try:
            start = int(next_token)
        except ValueError:
            start = 0
    end = start + page_size
    page = items[start:end]
    new_token = str(end) if end < len(items) else None
    return {"items": page, "next_token": new_token, "total": len(items)}


def dry_run_payload(tool: str, body: dict) -> dict:
    return {
        "dry_run": True,
        "tool": tool,
        "input": body,
        "items": [],
        "next_token": None,
        "message": f"Dry-run mode: {tool} not executed",
    }


def append_audit(settings: dict, entry: dict) -> None:
    path = audit_log_path(settings)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), **entry}
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def require_boto3():
    try:
        import boto3  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("boto3 not installed; run scripts/setup-aws-sidecar.sh") from exc


def boto_session(settings: dict, account_id: str | None = None):
    require_boto3()
    import boto3

    profile = profile_name(settings)
    if not profile:
        raise ValueError("aws profile not configured (Settings → Integrations)")
    if not profile_allowed(settings, profile):
        raise ValueError(f"profile {profile!r} is not in allowed_profiles")

    region = region_name(settings)
    session_kwargs: dict[str, Any] = {"profile_name": profile, "region_name": region}
    if account_id:
        if not account_allowed(settings, account_id):
            raise ValueError(f"account {account_id!r} is not in allowed_accounts")
        session_kwargs["profile_name"] = profile
    session = boto3.Session(**session_kwargs)
    sts = session.client("sts")
    identity = sts.get_caller_identity()
    if not account_allowed(settings, identity.get("Account", "")):
        raise ValueError(f"active account {identity.get('Account')} is not in allowed_accounts")
    return session


def client(settings: dict, service: str, account_id: str | None = None):
    session = boto_session(settings, account_id=account_id)
    return session.client(service, region_name=region_name(settings))
