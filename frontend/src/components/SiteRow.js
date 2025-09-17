import "./Dashboard.css";

const getStatusClass = (status) => {
  // treat known good statuses as green
  const good = ["Connected", "UptoDate", "NoAlerts", "Compliant"];
  const bad = ["NeedsAttention", "UpdateAvailable", "NonCompliant", "UpdateInProgress"];
  const unknown = ["Unknown", "NotRecentlyConnected"];
  if (good.includes(status)) return "status-green";
  if (bad.includes(status)) return "status-red";
  return "status-grey";
};

const SiteRow = ({ site }) => {
  // recommendations might be an object mapping resourceName -> [recs]
  const recsArr = site.Recommendations
    ? Object.values(site.Recommendations).flat()
    : [];

  // format health score (rounded)
  const healthScore = site.SiteHealthScore !== undefined && site.SiteHealthScore !== null
    ? Number(site.SiteHealthScore).toFixed(2)
    : "N/A";

  return (
    <div className="site-row">
      <span className="site-name">{site.SiteName}</span>

      {/* Health Score */}
      <span className="site-health">
        {healthScore}
      </span>

      {/* Status columns (show raw string from backend) */}
      <span className={`status-text ${getStatusClass(site.Connectivity)}`}>
        {site.Connectivity || "Unknown"}
      </span>
      <span className={`status-text ${getStatusClass(site.Update)}`}>
        {site.Update || "Unknown"}
      </span>
      <span className={`status-text ${getStatusClass(site.Alerts)}`}>
        {site.Alerts || "Unknown"}
      </span>
      <span className={`status-text ${getStatusClass(site.Security)}`}>
        {site.Security || "Unknown"}
      </span>

      {/* Recommendations as bullet points */}
      <div className="recommendation">
        {recsArr.length === 0 ? (
          <em>No recommendations</em>
        ) : (
          <ul>
            {recsArr.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default SiteRow;
