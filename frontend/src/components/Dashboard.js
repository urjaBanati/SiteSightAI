import { useEffect, useState } from "react";
import "./Dashboard.css";
import SiteRow from "./SiteRow";

const Dashboard = () => {
  const [sites, setSites] = useState([]);

  useEffect(() => {
    fetch("/ranked_sites.json", { cache: "no-store" }) // served from public folder
      .then((res) => res.json())
      .then((data) => {
        console.log("Fetched sites:", data);
        setSites(data);
      })
      .catch((err) => console.error("Error loading JSON:", err));
  }, []);

  return (
    <div className="dashboard">
      <h1 className="dashboard-title">Site AI Dashboard</h1>
      <div className="table-container">
        <div className="table-header">
          <span>Site Name</span>
          <span>Health Score</span>
          <span>Connectivity</span>
          <span>Update</span>
          <span>Alerts</span>
          <span>Security</span>
          <span>Recommendation</span>
        </div>

        <div className="table-body">
          {sites.map((site, i) => (
            <SiteRow key={i} site={site} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
