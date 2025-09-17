import { useEffect, useState } from "react";
import "./Dashboard.css";
import SiteRow from "./SiteRow";

const Dashboard = () => {
  const [sites, setSites] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/",  { cache: "no-store" })
      .then((res) => res.json())
      .then((data) => {
        console.log("Fetched sites:", data.slice(0, 3));
        setSites(data);
      })
      .catch((err) => console.error("Error fetching data:", err));
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
        {sites.map((site) => (
          <SiteRow key={site.SiteName} site={site} />
        ))}
      </div>
    </div>
  );
};

export default Dashboard;


// import { useEffect, useState } from "react";
// import "./Dashboard.css";
// import SiteRow from "./SiteRow";

// const Dashboard = () => {
//   const [sites, setSites] = useState([]);

//   useEffect(() => {
//     fetch("http://127.0.0.1:8000/") // backend endpoint returning ranked sites
//       .then((res) => res.json())
//       .then((data) => {
//         setSites(data); // backend already ranks them
//       })
//       .catch((err) => console.error("Error fetching data:", err));
//   }, []);

//   return (
//     <div className="dashboard">
//       <h1 className="dashboard-title">SiteSightAI Dashboard</h1>

//       <div className="table-container">
//         {/* HEADER - column order must match SiteRow */}
//         <div className="table-header">
//           <span>Site Name</span>
//           <span>Health Score</span>
//           <span>Connectivity</span>
//           <span>Update</span>
//           <span>Alerts</span>
//           <span>Security</span>
//           <span>Recommendations</span>
//         </div>

//         {/* ROWS */}
//         <div className="table-body">
//           {sites.map((site) => (
//             <SiteRow key={site.SiteName} site={site} />
//           ))}
//         </div>
//       </div>
//     </div>
//   );
// };

// export default Dashboard;
