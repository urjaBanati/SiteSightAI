from fastapi import FastAPI
from fastapi.responses import JSONResponse
import json
import pandas as pd
import joblib
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SiteSightAI Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or your frontend URL
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
connectivity_map = {"Connected": 1, "NeedsAttention": 0.5, "NotRecentlyConnected": 0}
update_map = {"UptoDate": 1, "UpdateAvailable": 0.5, "NeedsAttention": 0.5, "Unknown": 0, "UpdateInProgress": 0.5}
alert_map = {"NoAlerts": 1, "NeedsAttention": 0.5}
security_map = {"Compliant": 1, "NonCompliant": 0.5}

# -----------------------------
# Predefined recommendations (fallback)
# -----------------------------
recommendations = {
    "Connectivity": [
        "Check site network/firewall",
        "Verify DNS resolution",
        "Inspect router/switch logs"
    ],
    "Update": [
        "Check for recent update availability",
        "Verify if update download failed",
        "Check permissions for update installation"
    ],
    "Alerts": [
        "Review alert logs for recurring issues",
        "Classify alerts by severity",
        "Escalate high-priority alerts"
    ],
    "Security": [
        "Check patch compliance",
        "Validate access control policies",
        "Run vulnerability scan"
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

def predict_recommendations_ml(resource):
    """Use trained RandomForest model to predict recommendations"""
    features = pd.DataFrame([{
        "Connectivity": resource["Connectivity"],
        "Update": resource["Update"],
        "Alerts": resource["Alerts"],
        "Security": resource["Security"]
    }])
    features = pd.get_dummies(features).reindex(columns=rec_features, fill_value=0)
    pred = rec_model.predict(features)
    recs = mlb.inverse_transform(pred)
    return recs[0] if recs else ["No action required"]

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
    site_df["SiteHealthScore"] = site_df[["ConnectivityScore","UpdateScore","AlertScore","SecurityScore"]].mean(axis=1)
    site_df["RankLabel"] = site_df["SiteHealthScore"].apply(map_health_to_label)

    # One-hot encode resource types for ranking
    all_types = sorted(set([rtype for sublist in site_df["ResourceType"] for rtype in sublist]))
    for t in all_types:
        site_df[f"Type_{t}"] = site_df["ResourceType"].apply(lambda x: 1 if t in x else 0)

    feature_cols = ["ConnectivityScore","UpdateScore","AlertScore","SecurityScore"] + [f"Type_{t}" for t in all_types]
    X_rank = site_df[feature_cols]

    # Predict ranking scores
    site_df["RankScore"] = ranker.predict(X_rank)
    ranked_df = site_df.sort_values(by="RankScore", ascending=False)

    response = []
    for _, row in ranked_df.iterrows():
        health_scores = {
            "Connectivity": round(row["ConnectivityScore"], 2),
            "Update": round(row["UpdateScore"], 2),
            "Alerts": round(row["AlertScore"], 2),
            "Security": round(row["SecurityScore"], 2)
        }

        # Get ML-powered recommendations for each weak signal
        site_resources = df[df["SiteName"] == row["SiteName"]]
        recs_per_site = {}
        for _, res in site_resources.iterrows():
            recs_per_site[res["ResourceName"]] = predict_recommendations_ml(res)

        response.append({
            "SiteName": row["SiteName"],
            "RankScore": round(float(row["RankScore"]), 4),
            "SiteHealthScore": round(float(row["SiteHealthScore"]), 2),
            "HealthSignals": health_scores,
            "Connectivity": row["ConnectivityScore"],
            "Update": row["UpdateScore"],
            "Alerts": row["AlertScore"],
            "Security": row["SecurityScore"],
            "Recommendations": recs_per_site
        })

    return JSONResponse(content=response)
