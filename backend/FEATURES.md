SiteSightAI — Feature Extraction & Data Schema

Overview

This document describes the sample feature set used for ranking Site urgency and where to find the dummy data used by the prototype.

Data location

- backend/data/sites.json — example site telemetry rows (one object per site).

Per-row schema (JSON keys)

- site_id (string): Unique site identifier.
- connectivity_score (float 0.0-1.0): Higher = worse connectivity (normalized). Example: packet loss + latency combined.
- update_score (float 0.0-1.0): Higher = more out-of-date (higher means worse).
- alert_score (float 0.0-1.0): Higher = more alerts / higher severity.
- security_score (float 0.0-1.0): Higher = worse security posture (vulnerabilities/low defender score).
- label (int): Relevance / urgency target for learning-to-rank. Higher = more urgent (used as label in LambdaMART).
- group_id (int|string): Grouping ID for ranking (e.g., customer or region). Used to form LightGBM groups.
- resources (array of strings): Resource types present at the site (vm, container, storage, log_analytics, etc.). Useful for infra-suggestion rules.
- notes (string): Human notes; optional.

Feature engineering guidance

- Normalize raw telemetry to [0,1] where 1 = worst state needing attention.
- Consider additional derived features: rolling alert counts (24h), critical_alert_ratio, vuln_count, avg_patch_age_days, latency_ms.
- Encode categorical resource types with multi-hot vectors or presence flags.

ML training tips (LambdaMART)

- Use `group_id` to build LightGBM groups: group sizes = number of sites per group.
- Labels should reflect relative urgency per group (higher label = higher urgency).
- For small datasets, synthesize more rows for prototyping and validation.

Using the dummy file

- The prototype ranking script expects features: connectivity_score, update_score, alert_score, security_score.
- Update backend/data/sites.json with real telemetry or export from monitoring systems.

Next steps

- Implement `backend/ml/ranker.py` to train LightGBM ranker from this schema.
- Implement `backend/recommender/rules.yaml` to map feature thresholds to remediation suggestions.

