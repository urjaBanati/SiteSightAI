// src/components/HealthButton.js
import "./HealthButton.css";

const HealthButton = ({ label, value }) => {
  const getColor = val => {
    if (val >= 0.85) return "#0a84ff"; // healthy - blue
    if (val >= 0.7) return "#1e3a8a"; // moderate - dark blue
    if (val >= 0.5) return "#ff9500"; // needs attention - orange
    return "#ff3b30"; // bad - red
  };

  return (
    <div className="health-button" style={{ backgroundColor: getColor(value) }}>
      {label}: {value}
    </div>
  );
};

export default HealthButton;
