"""AWS sidecar route dispatcher."""
from __future__ import annotations

from routes import cost, iac, orgs, read_tools, security, write_tools

POST_ROUTES = {
    "/api/aws/describe-ec2-instances": read_tools.describe_ec2_instances,
    "/api/aws/list-s3-buckets": read_tools.list_s3_buckets,
    "/api/aws/get-lambda-config": read_tools.get_lambda_config,
    "/api/aws/list-lambda-functions": read_tools.list_lambda_functions,
    "/api/aws/describe-iam-role": read_tools.describe_iam_role,
    "/api/aws/describe-cloudformation-stack": read_tools.describe_cloudformation_stack,
    "/api/aws/get-caller-identity": read_tools.get_caller_identity,
    "/api/aws/scan-iac-workspace": iac.scan_iac_workspace,
    "/api/aws/correlate-iac-resource": iac.correlate_iac_resource,
    "/api/aws/get-cost-summary": cost.get_cost_summary,
    "/api/aws/list-security-hub-findings": security.list_security_hub_findings,
    "/api/aws/list-guardduty-findings": security.list_guardduty_findings,
    "/api/aws/analyze-iam-policy": security.analyze_iam_policy,
    "/api/aws/list-organization-accounts": orgs.list_organization_accounts,
    "/api/aws/assume-account-context": orgs.assume_account_context,
    "/api/aws/ec2-stop-instance": write_tools.ec2_stop_instance,
    "/api/aws/lambda-update-function-configuration": write_tools.lambda_update_function_configuration,
}


def handle_get(handler, path: str, settings: dict, pack_dir: str) -> None:
    if path == "/api/aws/status":
        handler._json(
            200,
            {
                "ok": True,
                "dry_run": settings.get("aws_dry_run"),
                "read_only": settings.get("aws_read_only", True),
            },
        )
        return
    handler._json(404, {"error": "not found"})


def handle_post(handler, path: str, body: dict, settings: dict, pack_dir: str) -> None:
    fn = POST_ROUTES.get(path)
    if fn is None:
        handler._json(404, {"error": "not found"})
        return
    try:
        result = fn(body, settings, pack_dir)
        handler._json(200, result)
    except PermissionError as exc:
        handler._json(403, {"error": str(exc)})
    except ValueError as exc:
        handler._json(400, {"error": str(exc)})
    except RuntimeError as exc:
        handler._json(503, {"error": str(exc)})
    except Exception as exc:  # noqa: BLE001
        handler._json(500, {"error": str(exc)})
