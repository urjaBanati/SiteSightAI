import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.ensemble import RandomForestClassifier
import lightgbm as lgb
import joblib

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

recommendations = {
    "Connectivity": ["Check site network/firewall","Verify DNS resolution","Inspect router/switch logs"],
    "Update": ["Check for recent update availability","Verify if update download failed","Check permissions for update installation"],
    "Alerts": ["Review alert logs for recurring issues","Classify alerts by severity","Escalate high-priority alerts"],
    "Security": ["Check patch compliance","Validate access control policies","Run vulnerability scan"]
}

# -----------------------------
# Helpers
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
            flattened_data.append({
                "SiteName": site_name,
                "ResourceName": resource["ResourceName"],
                "ResourceType": resource["ResourceType"],
                "Connectivity": resource["Connectivity"]["status"],
                "Update": resource["Update"]["status"],
                "Alerts": resource["Alerts"]["status"],
                "Security": resource["Security"]["status"],
                "ConnectivityScore": connectivity_map.get(resource["Connectivity"]["status"], 0),
                "UpdateScore": update_map.get(resource["Update"]["status"], 0),
                "AlertScore": alert_map.get(resource["Alerts"]["status"], 0),
                "SecurityScore": security_map.get(resource["Security"]["status"], 0),
                "ResourceHealthScore": round(calculate_resource_score(resource), 2)
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
    if resource["Connectivity"] == "NotRecentlyConnected":
        recs.append(recommendations["Connectivity"][0])
    if resource["Update"] in ["NeedsAttention", "UpdateInProgress"]:
        recs.append(recommendations["Update"][1])
    if resource["Alerts"] == "NeedsAttention":
        recs.append(recommendations["Alerts"][0])
    if resource["Security"] == "NonCompliant":
        recs.append(recommendations["Security"][0])
    if not recs:
        recs.append("No action required")
    return recs[:3]

# -----------------------------
# Build dataset
# -----------------------------
df = flatten_sites_json(sites)
df["Recommendations"] = df[["Connectivity", "Update", "Alerts", "Security"]].apply(
    lambda row: rule_based_recommendations(row), axis=1
)

# Recommendation Model (Random Forest)
X = pd.get_dummies(df[["Connectivity", "Update", "Alerts", "Security"]])
mlb = MultiLabelBinarizer()
y = mlb.fit_transform(df["Recommendations"])
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

rec_model = RandomForestClassifier(n_estimators=100, random_state=42)
rec_model.fit(X_train, y_train)

# Ranking Model (LambdaMART)
site_df = df.groupby("SiteName").agg({
    "ConnectivityScore": "mean",
    "UpdateScore": "mean",
    "AlertScore": "mean",
    "SecurityScore": "mean",
    "ResourceType": lambda x: list(x)
}).reset_index()
site_df["SiteHealthScore"] = site_df[["ConnectivityScore","UpdateScore","AlertScore","SecurityScore"]].mean(axis=1)
site_df["RankLabel"] = site_df["SiteHealthScore"].apply(map_health_to_label)
all_types = sorted(set([rtype for sublist in site_df["ResourceType"] for rtype in sublist]))
for t in all_types:
    site_df[f"Type_{t}"] = site_df["ResourceType"].apply(lambda x: 1 if t in x else 0)

feature_cols = ["ConnectivityScore","UpdateScore","AlertScore","SecurityScore"] + [f"Type_{t}" for t in all_types]
X_rank = site_df[feature_cols]
y_rank = site_df["RankLabel"]
group = [len(site_df)]
lgb_train = lgb.Dataset(X_rank, y_rank, group=group)

params = {"objective": "lambdarank","metric": "ndcg","learning_rate": 0.1,"num_leaves": 31,"min_data_in_leaf": 1}
ranker = lgb.train(params, lgb_train, num_boost_round=50)

# -----------------------------
# Save models
# -----------------------------
joblib.dump(rec_model, "rec_model.pkl")
joblib.dump(mlb, "mlb.pkl")
joblib.dump(X.columns, "rec_features.pkl")
joblib.dump(ranker, "ranker.pkl")
joblib.dump(feature_cols, "rank_features.pkl")

print("✅ Models trained and saved.")
