"""Gated mutating AWS operations with audit log."""
from __future__ import annotations

from aws_common import (
    append_audit,
    client,
    dry_run_enabled,
    read_only_enabled,
    write_enabled,
)


def _require_write(body: dict, settings: dict, tool: str) -> None:
    if read_only_enabled(settings) and not write_enabled(settings):
        raise PermissionError("write operations disabled (enable in Settings → Integrations)")
    if not write_enabled(settings):
        raise PermissionError("aws_write_enabled must be true for mutating tools")
    token = str(body.get("confirm_token", "") or "").strip()
    if not token:
        raise PermissionError("confirm_token required — user must explicitly approve this change")
    append_audit(
        settings,
        {
            "tool": tool,
            "confirm_token": token,
            "args": {k: v for k, v in body.items() if k != "confirm_token"},
        },
    )


def ec2_stop_instance(body: dict, settings: dict, pack_dir: str) -> dict:
    tool = "ec2_stop_instance"
    instance_id = str(body.get("instance_id", "") or "").strip()
    if not instance_id:
        raise ValueError("missing required parameter: instance_id")
    if dry_run_enabled(settings):
        return {"dry_run": True, "tool": tool, "instance_id": instance_id, "state": "stopping"}
    _require_write(body, settings, tool)
    ec2 = client(settings, "ec2")
    resp = ec2.stop_instances(InstanceIds=[instance_id])
    state = (resp.get("StoppingInstances") or [{}])[0]
    return {
        "instance_id": instance_id,
        "previous_state": (state.get("PreviousState") or {}).get("Name"),
        "current_state": (state.get("CurrentState") or {}).get("Name"),
    }


def lambda_update_function_configuration(body: dict, settings: dict, pack_dir: str) -> dict:
    tool = "lambda_update_function_configuration"
    fn = str(body.get("function_name", "") or "").strip()
    if not fn:
        raise ValueError("missing required parameter: function_name")
    if dry_run_enabled(settings):
        return {"dry_run": True, "tool": tool, "function_name": fn}
    _require_write(body, settings, tool)
    lam = client(settings, "lambda")
    params = {"FunctionName": fn}
    if "environment" in body:
        params["Environment"] = body["environment"]
    if "timeout" in body:
        params["Timeout"] = int(body["timeout"])
    if "memory_size" in body:
        params["MemorySize"] = int(body["memory_size"])
    resp = lam.update_function_configuration(**params)
    return {
        "function_name": resp.get("FunctionName"),
        "last_modified": resp.get("LastModified"),
        "state": resp.get("State"),
    }
