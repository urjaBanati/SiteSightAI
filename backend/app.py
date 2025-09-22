from fastapi import FastAPI
from fastapi.responses import JSONResponse
import json
import pandas as pd
import joblib
import random
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SiteSightAI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow frontend access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Load trained models
# -----------------------------
rec_model = joblib.load("rec_model.pkl")
mlb = joblib.load("mlb.pkl")
rec_features = list(joblib.load("rec_features.pkl"))
ranker = joblib.load("ranker.pkl")
rank_features = list(joblib.load("rank_features.pkl"))

# -----------------------------
# Load sites JSON
# -----------------------------
with open("data/sites_clean.json") as f:
    sites = json.load(f)

# -----------------------------
# Weights and mappings
# -----------------------------
weights = {"Connectivity": 0.3, "Update": 0.3, "Alerts": 0.2, "Security": 0.2}
connectivity_map = {"Connected": 1, "NeedsAttention": 0.5, "NotRecentlyConnected": 0.6}
update_map = {"UptoDate": 1, "UpdateAvailable": 0.5, "NeedsAttention": 0.5, "Unknown": 0, "UpdateInProgress": 0.5}
alert_map = {"NoAlerts": 1, "NeedsAttention": 0.5}
security_map = {"Compliant": 1, "NonCompliant": 0.5}

# -----------------------------
# Predefined recommendations (fallback)
# -----------------------------
recommendations = {
    "Connectivity": [
        "Check site network/firewall", "Verify DNS resolution", "Inspect router/switch logs",
        "Check ISP/service provider status", "Run ping and traceroute diagnostics", "Test bandwidth and latency",
        "Validate VPN or private link tunnels", "Check DHCP/Static IP configuration", "Review load balancer health",
        "Examine physical cabling/ports", "Monitor packet loss and jitter", "Audit QoS or traffic shaping policies",
        "Verify SSL/TLS handshake for secure connections", "Confirm routing table consistency",
        "Check wireless interference (if Wi-Fi dependent)"
    ],
    "Update": [
        "Check for recent update availability", "Verify if update download failed", "Check permissions for update installation",
        "Confirm device has sufficient disk space", "Validate system date/time (NTP sync)", "Review update installation logs",
        "Restart services post-update if required", "Ensure rollback/recovery points are set",
        "Check dependency patches or prerequisites", "Cross-check update version compatibility",
        "Audit devices with pending reboots", "Review group policy or WSUS configurations",
        "Check update throttling or bandwidth caps", "Ensure security patches applied before deadlines",
        "Test update in staging before full rollout"
    ],
    "Alerts": [
        "Review alert logs for recurring issues", "Classify alerts by severity", "Escalate high-priority alerts",
        "Set alert suppression for false positives", "Define auto-remediation playbooks", "Tag alerts with responsible owners",
        "Check alert thresholds and fine-tune", "Validate alert integration with ticketing system",
        "Review alert correlation across systems", "Verify escalation paths for after-hours",
        "Archive and report historical alerts", "Perform RCA (Root Cause Analysis) on repeated alerts",
        "Ensure monitoring agents are healthy", "Simulate incident scenarios for alert validation",
        "Audit alert notifications (email/SMS/webhook)"
    ],
    "Security": [
        "Check patch compliance", "Validate access control policies", "Run vulnerability scan",
        "Verify antivirus/EDR signatures updated", "Confirm encryption at rest and in transit",
        "Audit expired or weak TLS certificates", "Check multi-factor authentication enforcement",
        "Review firewall/NSG rules", "Audit privileged account usage", "Ensure least privilege principle applied",
        "Check endpoint hardening (disable unused ports)", "Run penetration test in staging environment",
        "Review SIEM dashboards for anomalies", "Verify data backup encryption",
        "Check compliance with GDPR/ISO/NIST/PCI standards"
    ]
}

# -----------------------------
# Helper functions
# -----------------------------
def calculate_resource_score(resource):
    return (
        connectivity_map.get(resource["Connectivity"]["status"], 0) * weights["Connectivity"] +
        update_map.get(resource["Update"]["status"], 0) * weights["Update"] +
        alert_map.get(resource["Alerts"]["status"], 0) * weights["Alerts"] +
        security_map.get(resource["Security"]["status"], 0) * weights["Security"]
    )

def flatten_sites_json(sites):
    flattened_data = []
    for site in sites:
        site_name = site.get("SiteName")
        for resource in site.get("Resources", []):
            connectivity_score = connectivity_map.get(resource["Connectivity"]["status"], 0)
            update_score = update_map.get(resource["Update"]["status"], 0)
            alert_score = alert_map.get(resource["Alerts"]["status"], 0)
            security_score = security_map.get(resource["Security"]["status"], 0)
            resource_score = calculate_resource_score(resource)

            flattened_data.append({
                "SiteName": site_name,
                "ResourceName": resource["ResourceName"],
                "ResourceType": resource["ResourceType"],
                "Connectivity": resource["Connectivity"]["status"],
                "Update": resource["Update"]["status"],
                "Alerts": resource["Alerts"]["status"],
                "Security": resource["Security"]["status"],
                "ConnectivityScore": connectivity_score,
                "UpdateScore": update_score,
                "AlertScore": alert_score,
                "SecurityScore": security_score,
                "ResourceHealthScore": round(resource_score, 2)
            })
    return pd.DataFrame(flattened_data)

def map_health_to_label(score):
    if score < 0.5:
        return 3
    elif score < 0.7:
        return 2
    elif score < 0.85:
        return 1
    else:
        return 0

def rule_based_recommendations(resource):
    recs = []
    if resource["Connectivity"] in ["NotRecentlyConnected", "NeedsAttention"]:
        recs.append(random.choice(recommendations["Connectivity"]))
    if resource["Update"] in ["NeedsAttention", "UpdateInProgress", "UpdateAvailable"]:
        recs.append(random.choice(recommendations["Update"]))
    if resource["Alerts"] == "NeedsAttention":
        recs.append(random.choice(recommendations["Alerts"]))
    if resource["Security"] == "NonCompliant":
        recs.append(random.choice(recommendations["Security"]))
    if not recs:
        recs.append("No action required")
    return recs[:3]

def predict_recommendations_ml(resource):
    """Use trained RandomForest model to predict recommendations, fallback to rule-based if empty"""
    features = pd.DataFrame([{
        "Connectivity": resource["Connectivity"],
        "Update": resource["Update"],
        "Alerts": resource["Alerts"],
        "Security": resource["Security"]
    }])
    features = pd.get_dummies(features).reindex(columns=rec_features, fill_value=0)

    pred = rec_model.predict(features)
    recs = mlb.inverse_transform(pred)

    if not recs or not recs[0]:
        return rule_based_recommendations(resource.to_dict())
    return recs[0]

# -----------------------------
# Endpoint
# -----------------------------
@app.get("/")
def ranked_sites():
    df = flatten_sites_json(sites)

    # Aggregate per site
    site_df = df.groupby("SiteName").agg({
        "ConnectivityScore": "mean",
        "UpdateScore": "mean",
        "AlertScore": "mean",
        "SecurityScore": "mean",
        "ResourceType": lambda x: list(x)
    }).reset_index()

    # Compute site-level health score
    site_df["SiteHealthScore"] = site_df[
        ["ConnectivityScore", "UpdateScore", "AlertScore", "SecurityScore"]
    ].mean(axis=1)
    site_df["RankLabel"] = site_df["SiteHealthScore"].apply(map_health_to_label)

    # One-hot encode resource types
    all_types = sorted(set([rtype for sublist in site_df["ResourceType"] for rtype in sublist]))
    for t in all_types:
        site_df[f"Type_{t}"] = site_df["ResourceType"].apply(lambda x: 1 if t in x else 0)

     # 🔹 Use the exact rank_features.pkl from training
    X_rank = site_df.reindex(columns=rank_features, fill_value=0)

    # Predict ranking scores with LambdaMART model
    site_df["RankScore"] = ranker.predict(X_rank)

    # 🔹 Sort by SiteHealthScore ascending (smallest first)
    ranked_df = site_df.sort_values(by="SiteHealthScore", ascending=True)

    response = []
    for _, row in ranked_df.iterrows():
        health_scores = {
            "Connectivity": round(row["ConnectivityScore"], 2),
            "Update": round(row["UpdateScore"], 2),
            "Alerts": round(row["AlertScore"], 2),
            "Security": round(row["SecurityScore"], 2)
        }

        # Get recommendations per resource
        site_resources = df[df["SiteName"] == row["SiteName"]]
        recs_per_site = {}
        for _, res in site_resources.iterrows():
            recs_per_site[res["ResourceName"]] = [
                f"{r}" for r in predict_recommendations_ml(res)
            ]

        response.append({
            "SiteName": row["SiteName"],
            "RankScore": round(float(row["RankScore"]), 4),
            "SiteHealthScore": round(float(row["SiteHealthScore"]), 2),
            "HealthSignals": health_scores,
            "Connectivity": site_resources["Connectivity"].mode()[0] if not site_resources.empty else "Unknown",
            "Update": site_resources["Update"].mode()[0] if not site_resources.empty else "Unknown",
            "Alerts": site_resources["Alerts"].mode()[0] if not site_resources.empty else "Unknown",
            "Security": site_resources["Security"].mode()[0] if not site_resources.empty else "Unknown",
            "Recommendations": recs_per_site
        })

    # 🔹 Save the entire response once (not inside loop!)
    with open("ranked_sites.json", "w") as f:
        json.dump(response, f, indent=2)
    with open("../frontend/public/ranked_sites.json", "w") as f:
        json.dump(response, f, indent=2)

    return JSONResponse(content=response)
