import pandas as pd
import ast
import random
import json

# Load CSV
df = pd.read_csv("sites_telemetry_data.csv")

# Status pools
connectivity_statuses = ["Connected", "NotRecentlyConnected", "NeedsAttention"]
update_statuses = ["Unknown", "UpdateAvailable", "UptoDate", "UpdateInProgress", "NeedsAttention"]
alert_statuses = ["NoAlerts", "NeedsAttention"]
security_statuses = ["Compliant", "NonCompliant"]

# Dictionary to store structured JSON
sites_dict = {}

for _, row in df.iterrows():
    site_name = str(row["Name"]).strip()
    resource_type_json = str(row["ResourceTypeCount"]).strip()

    # Parse JSON safely
    try:
        resource_types = ast.literal_eval(resource_type_json)
    except Exception:
        resource_types = {}

    if site_name not in sites_dict:
        sites_dict[site_name] = {"SiteName": site_name, "Resources": []}

    # Add only **one resource per type**
    for r_type in resource_types.keys():
        # Check if resource type already added
        if any(res["ResourceType"] == r_type for res in sites_dict[site_name]["Resources"]):
            continue

        resource_entry = {
            "ResourceName": f"{site_name}-{r_type.split('/')[-1]}",
            "ResourceType": r_type,
            "Connectivity": {"status": random.choice(connectivity_statuses)},
            "Update": {"status": random.choice(update_statuses)},
            "Alerts": {"status": random.choice(alert_statuses)},
            "Security": {"status": random.choice(security_statuses)},
        }
        sites_dict[site_name]["Resources"].append(resource_entry)

# Convert dict → list for JSON
site_list = list(sites_dict.values())

# Save JSON
with open("sites_clean.json", "w") as f:
    json.dump(site_list, f, indent=2)

print("✅ Nested JSON created: sites_clean.json")
