import React, { useState } from 'react';
import CategoryCoverage from './CategoryCoverage';
import EnrollmentAnalytics from './EnrollmentAnalytics';

// Define available majors (mapping code to full name)
const majors = {
  "is": "Information Systems",
  "ba": "Business Administration",
  "cs": "Computer Science",
  "bio": "Biological Sciences"
};

const AnalyticsPage = () => {
  const [selectedMajor, setSelectedMajor] = useState("bio");
  const [semester, setSemester] = useState("");

  return (
    <div style={{ padding: "20px" }}>
      <h1>Analytics Dashboard</h1>
      <div style={{ marginBottom: "20px" }}>
        <label>
          Select Major:&nbsp;
          <select value={selectedMajor} onChange={e => setSelectedMajor(e.target.value)}>
            {Object.entries(majors).map(([code, name]) => (
              <option key={code} value={code}>{name}</option>
            ))}
          </select>
        </label>
        &nbsp;&nbsp;&nbsp;
        <label>
          Semester:&nbsp;
          <input
            type="text"
            value={semester}
            onChange={e => setSemester(e.target.value)}
            placeholder="e.g., F23"
          />
        </label>
      </div>
      <CategoryCoverage selectedMajor={selectedMajor} semester={semester} majors={majors} />
      <hr />
      <EnrollmentAnalytics />
    </div>
  );
};

export default AnalyticsPage;
