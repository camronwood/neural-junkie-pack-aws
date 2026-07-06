"""Typed read-only AWS resource tools."""
from __future__ import annotations

from typing import Any

from aws_common import (
    clamp_page_size,
    client,
    dry_run_enabled,
    dry_run_payload,
    paginate_result,
)


def describe_ec2_instances(body: dict, settings: dict, pack_dir: str) -> dict:
    tool = "describe_ec2_instances"
    if dry_run_enabled(settings):
        return dry_run_payload(tool, body)
    page_size = clamp_page_size(body.get("page_size"))
    next_token = body.get("next_token")
    ec2 = client(settings, "ec2")
    params: dict[str, Any] = {"MaxResults": page_size}
    if next_token:
        params["NextToken"] = str(next_token)
    instance_ids = body.get("instance_ids") or []
    if instance_ids:
        params["InstanceIds"] = [str(i) for i in instance_ids]
    filters = body.get("filters")
    if isinstance(filters, list) and filters:
        params["Filters"] = filters
    resp = ec2.describe_instances(**params)
    items = []
    for reservation in resp.get("Reservations", []):
        for inst in reservation.get("Instances", []):
            items.append(
                {
                    "instance_id": inst.get("InstanceId"),
                    "state": (inst.get("State") or {}).get("Name"),
                    "instance_type": inst.get("InstanceType"),
                    "private_ip": inst.get("PrivateIpAddress"),
                    "public_ip": inst.get("PublicIpAddress"),
                    "tags": inst.get("Tags", []),
                    "launch_time": str(inst.get("LaunchTime", "")),
                }
            )
    return {
        "items": items,
        "next_token": resp.get("NextToken"),
        "count": len(items),
    }


def list_s3_buckets(body: dict, settings: dict, pack_dir: str) -> dict:
    tool = "list_s3_buckets"
    if dry_run_enabled(settings):
        return {
            **dry_run_payload(tool, body),
            "items": [{"name": "example-bucket", "creation_date": "2026-01-01T00:00:00Z"}],
        }
    page_size = clamp_page_size(body.get("page_size"))
    next_token = body.get("next_token")
    s3 = client(settings, "s3")
    resp = s3.list_buckets()
    buckets = [
        {"name": b.get("Name"), "creation_date": str(b.get("CreationDate", ""))}
        for b in resp.get("Buckets", [])
    ]
    if next_token is not None or page_size:
        return paginate_result(buckets, page_size, str(next_token) if next_token else None)
    return {"items": buckets, "next_token": None, "count": len(buckets)}


def get_lambda_config(body: dict, settings: dict, pack_dir: str) -> dict:
    tool = "get_lambda_config"
    fn = str(body.get("function_name", "") or "").strip()
    if not fn:
        raise ValueError("missing required parameter: function_name")
    if dry_run_enabled(settings):
        return {
            **dry_run_payload(tool, body),
            "function_name": fn,
            "runtime": "python3.12",
            "handler": "app.handler",
        }
    lam = client(settings, "lambda")
    qualifier = str(body.get("qualifier", "") or "").strip()
    kwargs: dict[str, Any] = {"FunctionName": fn}
    if qualifier:
        kwargs["Qualifier"] = qualifier
    fn_resp = lam.get_function(**kwargs)
    cfg_resp = lam.get_function_configuration(**kwargs)
    return {
        "function_name": cfg_resp.get("FunctionName"),
        "runtime": cfg_resp.get("Runtime"),
        "handler": cfg_resp.get("Handler"),
        "memory_size": cfg_resp.get("MemorySize"),
        "timeout": cfg_resp.get("Timeout"),
        "role": cfg_resp.get("Role"),
        "environment": (cfg_resp.get("Environment") or {}).get("Variables", {}),
        "last_modified": cfg_resp.get("LastModified"),
        "code_location": (fn_resp.get("Code") or {}).get("Location"),
        "state": cfg_resp.get("State"),
    }


def list_lambda_functions(body: dict, settings: dict, pack_dir: str) -> dict:
    tool = "list_lambda_functions"
    if dry_run_enabled(settings):
        return {
            **dry_run_payload(tool, body),
            "items": [{"function_name": "example-fn", "runtime": "python3.12"}],
        }
    page_size = clamp_page_size(body.get("page_size"))
    lam = client(settings, "lambda")
    params: dict[str, Any] = {"MaxItems": page_size}
    if body.get("next_token"):
        params["Marker"] = str(body["next_token"])
    resp = lam.list_functions(**params)
    items = [
        {
            "function_name": f.get("FunctionName"),
            "runtime": f.get("Runtime"),
            "last_modified": f.get("LastModified"),
        }
        for f in resp.get("Functions", [])
    ]
    return {"items": items, "next_token": resp.get("NextMarker"), "count": len(items)}


def describe_iam_role(body: dict, settings: dict, pack_dir: str) -> dict:
    tool = "describe_iam_role"
    role = str(body.get("role_name", "") or "").strip()
    if not role:
        raise ValueError("missing required parameter: role_name")
    if dry_run_enabled(settings):
        return {**dry_run_payload(tool, body), "role_name": role, "arn": "arn:aws:iam::123456789012:role/example"}
    iam = client(settings, "iam")
    resp = iam.get_role(RoleName=role)
    role_obj = resp.get("Role", {})
    return {
        "role_name": role_obj.get("RoleName"),
        "arn": role_obj.get("Arn"),
        "create_date": str(role_obj.get("CreateDate", "")),
        "assume_role_policy": role_obj.get("AssumeRolePolicyDocument"),
        "max_session_duration": role_obj.get("MaxSessionDuration"),
    }


def describe_cloudformation_stack(body: dict, settings: dict, pack_dir: str) -> dict:
    tool = "describe_cloudformation_stack"
    stack = str(body.get("stack_name", "") or "").strip()
    if not stack:
        raise ValueError("missing required parameter: stack_name")
    if dry_run_enabled(settings):
        return {
            **dry_run_payload(tool, body),
            "stack_name": stack,
            "status": "CREATE_COMPLETE",
        }
    cfn = client(settings, "cloudformation")
    resp = cfn.describe_stacks(StackName=stack)
    stacks = resp.get("Stacks", [])
    if not stacks:
        return {"stack_name": stack, "found": False}
    s = stacks[0]
    return {
        "stack_name": s.get("StackName"),
        "stack_id": s.get("StackId"),
        "status": s.get("StackStatus"),
        "creation_time": str(s.get("CreationTime", "")),
        "last_updated": str(s.get("LastUpdatedTime", "")),
        "outputs": s.get("Outputs", []),
        "parameters": s.get("Parameters", []),
    }


def get_caller_identity(body: dict, settings: dict, pack_dir: str) -> dict:
    if dry_run_enabled(settings):
        return {
            "Account": "123456789012",
            "Arn": "arn:aws:sts::123456789012:assumed-role/example",
            "UserId": "AIDEXAMPLE",
            "dry_run": True,
        }
    sts = client(settings, "sts")
    return sts.get_caller_identity()
