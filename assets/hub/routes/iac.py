"""IaC scan and live-state correlation."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from aws_common import dry_run_enabled, dry_run_payload

_TF_RESOURCE = re.compile(
    r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{',
    re.MULTILINE,
)


def _scan_terraform(root: Path) -> list[dict]:
    items: list[dict] = []
    for path in root.rglob("*.tf"):
        if ".terraform" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in _TF_RESOURCE.finditer(text):
            items.append(
                {
                    "source": "terraform",
                    "file": str(path.relative_to(root)),
                    "resource_type": match.group(1),
                    "logical_id": match.group(2),
                }
            )
    return items


def _scan_cloudformation(root: Path) -> list[dict]:
    items: list[dict] = []
    patterns = ["template.yaml", "template.yml", "template.json"]
    for pattern in patterns:
        for path in root.rglob(pattern):
            if "node_modules" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            try:
                if path.suffix == ".json":
                    doc = json.loads(text)
                else:
                    import yaml  # type: ignore

                    doc = yaml.safe_load(text)
            except Exception:
                continue
            resources = (doc or {}).get("Resources") or {}
            for logical_id, spec in resources.items():
                items.append(
                    {
                        "source": "cloudformation",
                        "file": str(path.relative_to(root)),
                        "resource_type": spec.get("Type"),
                        "logical_id": logical_id,
                    }
                )
    return items


def _scan_cdk(root: Path) -> list[dict]:
    items: list[dict] = []
    cdk_out = root / "cdk.out"
    if not cdk_out.is_dir():
        return items
    for path in cdk_out.glob("*.template.json"):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for logical_id, spec in (doc.get("Resources") or {}).items():
            items.append(
                {
                    "source": "cdk",
                    "file": str(path.relative_to(root)),
                    "resource_type": spec.get("Type"),
                    "logical_id": logical_id,
                }
            )
    return items


def scan_iac_workspace(body: dict, settings: dict, pack_dir: str) -> dict:
    tool = "scan_iac_workspace"
    workspace_root = str(body.get("workspace_root", "") or "").strip()
    if not workspace_root:
        workspace_root = os.getcwd()
    root = Path(workspace_root).resolve()
    if dry_run_enabled(settings):
        return {
            **dry_run_payload(tool, body),
            "items": [
                {
                    "source": "terraform",
                    "file": "terraform/main.tf",
                    "resource_type": "aws_instance",
                    "logical_id": "web",
                }
            ],
        }
    items: list[dict] = []
    for scanner in (_scan_terraform, _scan_cloudformation, _scan_cdk):
        items.extend(scanner(root))
    return {"workspace_root": str(root), "items": items, "count": len(items)}


def correlate_iac_resource(body: dict, settings: dict, pack_dir: str) -> dict:
    tool = "correlate_iac_resource"
    resource_type = str(body.get("resource_type", "") or "").strip()
    resource_id = str(body.get("id_or_arn", "") or body.get("resource_id", "") or "").strip()
    declared = body.get("declared")
    if not resource_type or not resource_id:
        raise ValueError("resource_type and id_or_arn required")
    if dry_run_enabled(settings):
        return {
            **dry_run_payload(tool, body),
            "declared": declared,
            "live": {"state": "running"},
            "drift_summary": "dry-run: no live lookup",
        }
    from routes import read_tools

    live: dict[str, Any] | None = None
    drift = "unknown"
    rt = resource_type.lower()
    try:
        if "instance" in rt or rt == "aws_instance":
            live = read_tools.describe_ec2_instances(
                {"instance_ids": [resource_id], "page_size": 1},
                settings,
                pack_dir,
            )
            drift = "match" if live.get("items") else "missing_in_account"
        elif rt.endswith("s3::bucket") or rt == "aws_s3_bucket":
            live = read_tools.list_s3_buckets({}, settings, pack_dir)
            names = [b.get("name") for b in live.get("items", [])]
            drift = "match" if resource_id in names else "missing_in_account"
        elif "lambda" in rt:
            live = read_tools.get_lambda_config(
                {"function_name": resource_id}, settings, pack_dir
            )
            drift = "match" if live.get("function_name") else "missing_in_account"
        elif "iam::role" in rt or rt == "aws_iam_role":
            live = read_tools.describe_iam_role(
                {"role_name": resource_id.split("/")[-1]}, settings, pack_dir
            )
            drift = "match" if live.get("role_name") else "missing_in_account"
        else:
            drift = f"no correlator for {resource_type}"
    except Exception as exc:  # noqa: BLE001
        drift = f"lookup_error: {exc}"
    return {
        "resource_type": resource_type,
        "id_or_arn": resource_id,
        "declared": declared,
        "live": live,
        "drift_summary": drift,
    }
