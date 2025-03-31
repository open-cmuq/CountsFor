import React, { useState } from 'react';
import CategoryCoverage from './CategoryCoverage';
import EnrollmentAnalytics from './EnrollmentAnalytics';
import "../styles.css";

// Define available majors (mapping code to full name)
const majors = {
  "is": "Information Systems",
  "ba": "Business Administration",
  "cs": "Computer Science",
  "bio": "Biological Sciences"
};

const AnalyticsPage = () => {
  const [selectedMajor, setSelectedMajor] = useState("bio");

  return (
    <div className="table-container">
      <h1 className="title" style={{ marginBottom: "30px" }}>Analytics Dashboard</h1>

      {/* Category Coverage Section */}
      <div style={{ marginBottom: "40px" }}>
        <CategoryCoverage selectedMajor={selectedMajor} setSelectedMajor={setSelectedMajor} majors={majors} />
      </div>

      {/* Separator */}
      <hr style={{
        margin: "40px 0",
        border: "none",
        borderTop: "1px solid #ddd",
        width: "100%"
      }} />

      {/* Enrollment Analytics Section */}
      <div style={{ marginTop: "40px" }}>
        <EnrollmentAnalytics />
      </div>
    </div>
  );
};

export default AnalyticsPage;
