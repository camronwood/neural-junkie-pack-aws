"""Security Hub, GuardDuty, IAM policy analysis."""
from __future__ import annotations

import json
from typing import Any

from aws_common import clamp_page_size, client, dry_run_enabled, dry_run_payload


def list_security_hub_findings(body: dict, settings: dict, pack_dir: str) -> dict:
    tool = "list_security_hub_findings"
    if dry_run_enabled(settings):
        return {
            **dry_run_payload(tool, body),
            "items": [
                {
                    "id": "arn:aws:securityhub:example",
                    "severity": "HIGH",
                    "title": "Example finding",
                }
            ],
        }
    sh = client(settings, "securityhub")
    page_size = clamp_page_size(body.get("page_size"))
    filters: dict[str, Any] = {}
    severity = body.get("severity")
    if severity:
        filters["SeverityLabel"] = [{"Value": str(severity), "Comparison": "EQUALS"}]
    params: dict[str, Any] = {"MaxResults": page_size}
    if filters:
        params["Filters"] = filters
    if body.get("next_token"):
        params["NextToken"] = str(body["next_token"])
    ids_resp = sh.get_findings(**params)
    findings = ids_resp.get("Findings", [])
    items = [
        {
            "id": f.get("Id"),
            "severity": (f.get("Severity") or {}).get("Label"),
            "title": f.get("Title"),
            "resource": f.get("Resources", []),
            "updated_at": str(f.get("UpdatedAt", "")),
        }
        for f in findings
    ]
    return {"items": items, "next_token": ids_resp.get("NextToken"), "count": len(items)}


def list_guardduty_findings(body: dict, settings: dict, pack_dir: str) -> dict:
    tool = "list_guardduty_findings"
    if dry_run_enabled(settings):
        return {
            **dry_run_payload(tool, body),
            "items": [{"id": "example-finding", "severity": 5.0, "type": "Recon:EC2/PortProbeUnprotectedPort"}],
        }
    gd = client(settings, "guardduty")
    detectors = gd.list_detectors()
    detector_ids = detectors.get("DetectorIds") or []
    if not detector_ids:
        return {"items": [], "message": "no GuardDuty detector in region"}
    detector_id = detector_ids[0]
    list_params: dict[str, Any] = {"DetectorId": detector_id, "MaxResults": clamp_page_size(body.get("page_size"))}
    if body.get("next_token"):
        list_params["NextToken"] = str(body["next_token"])
    listed = gd.list_findings(DetectorId=detector_id, MaxResults=list_params["MaxResults"])
    finding_ids = listed.get("FindingIds") or []
    if not finding_ids:
        return {"items": [], "next_token": listed.get("NextToken")}
    details = gd.get_findings(DetectorId=detector_id, FindingIds=finding_ids[:50])
    items = [
        {
            "id": f.get("Id"),
            "type": f.get("Type"),
            "severity": f.get("Severity"),
            "title": f.get("Title"),
            "resource": f.get("Resource"),
        }
        for f in details.get("Findings", [])
    ]
    return {"items": items, "next_token": listed.get("NextToken"), "count": len(items)}


def analyze_iam_policy(body: dict, settings: dict, pack_dir: str) -> dict:
    tool = "analyze_iam_policy"
    policy_doc = body.get("policy_document")
    role_name = str(body.get("role_name", "") or "").strip()
    action_names = body.get("action_names") or ["s3:ListBucket", "ec2:DescribeInstances"]
    if dry_run_enabled(settings):
        return {
            **dry_run_payload(tool, body),
            "allowed": action_names,
            "denied": [],
        }
    iam = client(settings, "iam")
    if policy_doc is None and role_name:
        role = iam.get_role(RoleName=role_name)
        policy_doc = role.get("Role", {}).get("AssumeRolePolicyDocument")
    if isinstance(policy_doc, str):
        policy_doc = json.loads(policy_doc)
    if not isinstance(policy_doc, dict):
        raise ValueError("policy_document or role_name required")
    statements = policy_doc.get("Statement") or []
    if isinstance(statements, dict):
        statements = [statements]
    allowed: list[str] = []
    denied: list[str] = []
    for stmt in statements:
        effect = str(stmt.get("Effect", "Allow")).upper()
        actions = stmt.get("Action") or stmt.get("NotAction") or []
        if isinstance(actions, str):
            actions = [actions]
        for action in action_names:
            matched = any(
                a == "*" or a == action or (a.endswith("*") and action.startswith(a[:-1]))
                for a in actions
            )
            if matched:
                if effect == "DENY":
                    denied.append(action)
                else:
                    allowed.append(action)
    return {
        "role_name": role_name or None,
        "allowed": sorted(set(allowed)),
        "denied": sorted(set(denied)),
        "statement_count": len(statements),
    }
