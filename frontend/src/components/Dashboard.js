// src/components/Dashboard.js
import { useEffect, useState } from "react";
import "./Dashboard.css"; // we'll add styles here
import SiteCard from "./SiteCard";

const Dashboard = () => {
  const [sites, setSites] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/") // your backend
      .then(res => res.json())
      .then(data => {
        // sort descending by RankScore
        const sorted = data.sort((a, b) => b.RankScore - a.RankScore);
        setSites(sorted);
      })
      .catch(err => console.error("Error fetching sites:", err));
  }, []);

  return (
    <div className="dashboard">
      <h1 className="dashboard-title">SiteSight AI Dashboard</h1>
      <div className="site-list">
        {sites.map(site => (
          <SiteCard key={site.SiteName} site={site} />
        ))}
      </div>
    </div>
  );
};

export default Dashboard;
