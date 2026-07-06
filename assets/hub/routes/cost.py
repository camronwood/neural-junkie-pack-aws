"""Cost Explorer summaries."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from aws_common import client, dry_run_enabled, dry_run_payload


def get_cost_summary(body: dict, settings: dict, pack_dir: str) -> dict:
    tool = "get_cost_summary"
    end = str(body.get("end_date", "") or date.today().isoformat())
    start = str(
        body.get("start_date", "")
        or (date.fromisoformat(end) - timedelta(days=30)).isoformat()
    )
    granularity = str(body.get("granularity", "MONTHLY") or "MONTHLY")
    group_by = str(body.get("group_by", "SERVICE") or "SERVICE")
    if dry_run_enabled(settings):
        return {
            **dry_run_payload(tool, body),
            "results": [{"service": "Amazon EC2", "amount": "42.00", "unit": "USD"}],
        }
    ce = client(settings, "ce")
    params: dict[str, Any] = {
        "TimePeriod": {"Start": start, "End": end},
        "Granularity": granularity,
        "Metrics": ["UnblendedCost"],
        "GroupBy": [{"Type": "DIMENSION", "Key": group_by}],
    }
    resp = ce.get_cost_and_usage(**params)
    results = []
    for period in resp.get("ResultsByTime", []):
        for group in period.get("Groups", []):
            amount = (group.get("Metrics") or {}).get("UnblendedCost", {})
            results.append(
                {
                    "period_start": period.get("TimePeriod", {}).get("Start"),
                    "period_end": period.get("TimePeriod", {}).get("End"),
                    "key": group.get("Keys", [""])[0],
                    "amount": amount.get("Amount"),
                    "unit": amount.get("Unit"),
                }
            )
    return {"start_date": start, "end_date": end, "results": results, "count": len(results)}
