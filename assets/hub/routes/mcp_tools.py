"""Pack-owned MCP tool dispatch for the AWS hub sidecar."""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from routes import aws

TOOL_TO_PATH = {
    "aws_get_caller_identity": "/api/aws/get-caller-identity",
    "describe_ec2_instances": "/api/aws/describe-ec2-instances",
    "list_s3_buckets": "/api/aws/list-s3-buckets",
    "get_lambda_config": "/api/aws/get-lambda-config",
    "list_lambda_functions": "/api/aws/list-lambda-functions",
    "describe_iam_role": "/api/aws/describe-iam-role",
    "describe_cloudformation_stack": "/api/aws/describe-cloudformation-stack",
    "scan_iac_workspace": "/api/aws/scan-iac-workspace",
    "correlate_iac_resource": "/api/aws/correlate-iac-resource",
    "get_cost_summary": "/api/aws/get-cost-summary",
    "list_security_hub_findings": "/api/aws/list-security-hub-findings",
    "list_guardduty_findings": "/api/aws/list-guardduty-findings",
    "analyze_iam_policy": "/api/aws/analyze-iam-policy",
    "list_organization_accounts": "/api/aws/list-organization-accounts",
    "assume_account_context": "/api/aws/assume-account-context",
    "ec2_stop_instance": "/api/aws/ec2-stop-instance",
    "lambda_update_function_configuration": "/api/aws/lambda-update-function-configuration",
}


def tools_catalog(pack_dir: str) -> list[dict[str, Any]]:
    path = os.path.join(pack_dir, "assets", "mcp", "tools.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return list(data.get("tools") or [])


def handle_tools_get(handler, pack_dir: str) -> None:
    try:
        tools = tools_catalog(pack_dir)
        handler._json(200, {"ok": True, "tools": tools})
    except Exception as exc:  # noqa: BLE001
        handler._json(500, {"ok": False, "error": str(exc)})


def handle_call(handler, body: dict, settings: dict, pack_dir: str) -> None:
    name = str(body.get("name") or "").strip()
    args = body.get("arguments") if isinstance(body.get("arguments"), dict) else {}
    if not name:
        handler._json(400, {"ok": False, "error": "missing tool name"})
        return
    try:
        text = dispatch(name, args, settings, pack_dir)
        handler._json(200, {"ok": True, "text": text})
    except PermissionError as exc:
        handler._json(403, {"ok": False, "error": str(exc)})
    except ValueError as exc:
        handler._json(400, {"ok": False, "error": str(exc)})
    except RuntimeError as exc:
        handler._json(503, {"ok": False, "error": str(exc)})
    except Exception as exc:  # noqa: BLE001
        handler._json(500, {"ok": False, "error": str(exc)})


def dispatch(name: str, args: dict, settings: dict, pack_dir: str) -> str:
    if name == "aws_list_profiles":
        profiles = list_profiles()
        return "\n".join(profiles) if profiles else "No profiles found in ~/.aws/config"

    if name == "aws_sso_login_hint":
        profile = str(args.get("profile") or "").strip() or str(
            settings.get("aws_profile") or ""
        ).strip()
        if not profile:
            raise ValueError("configure aws profile in Settings → Integrations")
        msg = (
            f"Run in your terminal:\n\naws sso login --profile {profile}\n\n"
            "Then retry AWS tools."
        )
        start = str(settings.get("aws_sso_start_url") or "").strip()
        if start:
            msg += f"\nSSO start URL (reference): {start}"
        return msg

    if name == "aws_cli_query":
        return run_cli_query(args, settings)

    path = TOOL_TO_PATH.get(name)
    if path is None:
        raise ValueError(f"unknown tool: {name}")
    fn = aws.POST_ROUTES.get(path)
    if fn is None:
        raise ValueError(f"no route for tool: {name}")
    body = dict(args)
    if name == "aws_get_caller_identity" and body.get("profile"):
        # Profile overrides flow through settings copy for this call.
        settings = dict(settings)
        settings["aws_profile"] = str(body.get("profile")).strip()
    result = fn(body, settings, pack_dir)
    if isinstance(result, (dict, list)):
        return json.dumps(result, indent=2, default=str)
    return str(result)


def list_profiles() -> list[str]:
    home = Path.home()
    seen: set[str] = set()
    out: list[str] = []

    def add(name: str) -> None:
        name = name.strip()
        if not name or name in seen:
            return
        seen.add(name)
        out.append(name)

    config_path = home / ".aws" / "config"
    if config_path.is_file():
        section_re = re.compile(r"^\[(.+)\]\s*$")
        for line in config_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = section_re.match(line.strip())
            if not m:
                continue
            inner = m.group(1)
            if inner.startswith("profile "):
                add(inner[len("profile ") :])
            elif inner == "default":
                add("default")

    creds = home / ".aws" / "credentials"
    if creds.is_file():
        for line in creds.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip() == "[default]":
                add("default")
                break
    return out


def run_cli_query(args: dict, settings: dict) -> str:
    service = str(args.get("service") or "").strip()
    operation = str(args.get("operation") or "").strip()
    if not service or not operation:
        raise ValueError("service and operation required")
    cmd = ["aws", service, operation]
    extra = args.get("extra_args") or []
    if isinstance(extra, list):
        cmd.extend(str(x) for x in extra if str(x).strip())
    env = os.environ.copy()
    profile = str(settings.get("aws_profile") or "").strip()
    region = str(settings.get("aws_default_region") or "").strip()
    if profile:
        env["AWS_PROFILE"] = profile
    if region:
        env["AWS_DEFAULT_REGION"] = region
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "aws cli failed").strip()
        raise RuntimeError(err)
    return (proc.stdout or "").strip() or "(empty)"
