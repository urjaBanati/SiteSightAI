import { useState } from "react";
import "./Dashboard.css";

const getStatusClass = (status) => {
  const good = ["Connected", "UptoDate", "NoAlerts", "Compliant"];
  const bad = ["NeedsAttention", "UpdateAvailable", "NonCompliant", "UpdateInProgress"];
  const unknown = ["Unknown", "NotRecentlyConnected"];
  if (good.includes(status)) return "status-green";
  if (bad.includes(status)) return "status-red";
  return "status-grey";
};

const SiteRow = ({ site }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showRecs, setShowRecs] = useState(false);

  // Flatten recommendations
  const recsArr = site.Recommendations
    ? Object.values(site.Recommendations).flat()
    : [];

  // Format health score
  const healthScore =
    site.SiteHealthScore !== undefined && site.SiteHealthScore !== null
      ? Number(site.SiteHealthScore).toFixed(2)
      : "N/A";

  const handleAnalyze = () => {
    setIsAnalyzing(true);
    setShowRecs(false);
    setTimeout(() => {
      setIsAnalyzing(false);
      setShowRecs(true);
    }, 2000); // 2s fake delay
  };

  return (
    <div className="site-row">
      <span className="site-name">{site.SiteName}</span>

      {/* Health Score */}
      <span className="site-health">{healthScore}</span>

      {/* Status columns */}
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

      {/* Recommendations / Analyze */}
      <div className="recommendation">
        {!isAnalyzing && !showRecs && (
          <button className="analyze-btn" onClick={handleAnalyze}>
            Analyze
          </button>
        )}

        {isAnalyzing && (
          <em className="loading-text">
            <span className="spinner" /> Analyzing health score and status...
          </em>
        )}

        {showRecs && (
          recsArr.length === 0 ? (
            <em>No recommendations</em>
          ) : (
            <ul>
              {recsArr.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          )
        )}
      </div>
    </div>
  );
};

export default SiteRow;
