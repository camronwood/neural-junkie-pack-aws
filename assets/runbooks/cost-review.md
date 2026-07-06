# Cost review (read-only)

1. Confirm Cost Explorer IAM (`ce:GetCostAndUsage`) on the active SSO profile.
2. Call `get_cost_summary` with `start_date`, `end_date`, and optional `group_by` (`SERVICE`, `LINKED_ACCOUNT`).
3. Flag top 3 services by spend; note week-over-week deltas.
4. Cross-check with `@PlatformEngineer` for repo-side scaling changes (autoscaling, new services).

Do not mutate resources during cost review.
