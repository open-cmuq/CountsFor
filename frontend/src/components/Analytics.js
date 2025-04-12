import React, { useState, useEffect } from 'react';
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
  const [selectedMajor, setSelectedMajor] = useState(() => {
    return localStorage.getItem("analyticsMajor") || "bio";
  });

  // Save selected major to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem("analyticsMajor", selectedMajor);
  }, [selectedMajor]);

  return (
    <div className="analytics-container table-container">
      <h1 className="title" style={{ marginBottom: "30px" }}>Analyze Courses</h1>
      <p className="subtitle" style={{ marginTop: "-20px", marginBottom: "30px" }}>Visualize requirement coverage, enrollment trends, and course relationships.</p>

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
