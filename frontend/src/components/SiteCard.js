// src/components/SiteCard.js
import { useState } from "react";
import HealthButton from "./HealthButton";
import "./SiteCard.css";

const SiteCard = ({ site }) => {
  const [showInfo, setShowInfo] = useState(false);

  return (
    <div className="site-card">
      <div className="site-header">
        <h3>{site.SiteName}</h3>
        <div
          className="info-icon"
          onMouseEnter={() => setShowInfo(true)}
          onMouseLeave={() => setShowInfo(false)}
        >
          ℹ️
          {showInfo && (
            <div className="info-popup">
              {Object.entries(site.Recommendations).map(([key, recs]) => (
                <div key={key}>
                  <strong>{key}:</strong>
                  <ul>
                    {recs.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      <div className="health-buttons">
        <HealthButton label="Connectivity" value={site.HealthSignals.Connectivity} />
        <HealthButton label="Update" value={site.HealthSignals.Update} />
        <HealthButton label="Alerts" value={site.HealthSignals.Alerts} />
        <HealthButton label="Security" value={site.HealthSignals.Security} />
      </div>
    </div>
  );
};

export default SiteCard;
