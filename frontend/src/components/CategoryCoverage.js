import React, { useState, useEffect, useCallback } from 'react';
import Plot from 'react-plotly.js';
import { sortSemesters } from './utils/semesterUtils';
import "../styles.css";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const CategoryCoverage = ({ selectedMajor, setSelectedMajor, majors }) => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [semester, setSemester] = useState('');
  const [validSemesters, setValidSemesters] = useState([]);

  // Fetch available semesters
  useEffect(() => {
    const fetchSemesters = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/courses/semesters`);
        if (!response.ok) throw new Error("Failed to fetch semesters");
        const data = await response.json();
        // Sort semesters by most recent first
        const sortedSemesters = sortSemesters(data.semesters);

        // Check each semester for data
        const validSems = [];
        for (const sem of sortedSemesters) {
          const params = new URLSearchParams();
          params.append("major", selectedMajor);
          params.append("semester", sem);
          const coverageResponse = await fetch(`${API_BASE_URL}/analytics/course-coverage?${params.toString()}`);
          if (coverageResponse.ok) {
            const coverageData = await coverageResponse.json();
            // Only include semester if it has at least one course with non-zero count
            if (coverageData.coverage.some(item => item.num_courses > 0)) {
              validSems.push(sem);
            }
          }
        }
        setValidSemesters(validSems);
      } catch (error) {
        console.error("Error fetching semesters:", error);
        setValidSemesters([]);
      }
    };
    fetchSemesters();
  }, [selectedMajor]);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append("major", selectedMajor);
      if (semester) {
        params.append("semester", semester);
      }
      const response = await fetch(`${API_BASE_URL}/analytics/course-coverage?${params.toString()}`);
      if (!response.ok) throw new Error("Failed to fetch analytics data");
      const data = await response.json();
      setChartData(data);
    } catch (error) {
      console.error("Error fetching analytics:", error);
      setChartData(null);
    } finally {
      setLoading(false);
    }
  }, [selectedMajor, semester]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  // Prepare trace data if we have chartData
  let plotTrace = null;
  if (chartData && chartData.coverage) {
    // --- Aggregate data by the short label ---
    const aggregatedData = {};
    chartData.coverage.forEach(item => {
      const parts = item.requirement.split('---');
      const shortLabel = parts[parts.length - 1].trim();
      if (!aggregatedData[shortLabel]) {
        aggregatedData[shortLabel] = 0;
      }
      // Only add if num_courses is greater than 0 to avoid empty bars cluttering
      if (item.num_courses > 0) {
          aggregatedData[shortLabel] += item.num_courses;
      }
    });

    // --- Convert aggregated data to points, filter out zero counts, and sort ---
    const plotPoints = Object.entries(aggregatedData)
                             .filter(([label, count]) => count > 0) // Ensure no zero counts slip through
                             .map(([label, count]) => ({ label, count }))
                             .sort((a, b) => a.count - b.count); // Sort ascending by count

    // --- Generate plot data from aggregated points ---
    const xData = plotPoints.map(p => p.count);
    const yData = plotPoints.map(p => p.label);
    const colors = plotPoints.map((_, index) =>
      index % 2 === 0 ? '#4A68FB' : '#D3D3D3' // Blue and Light Grey
    );

    plotTrace = {
      x: xData,
      y: yData,
      type: 'bar',
      orientation: 'h',
      hovertemplate: 'Count: %{x}<extra></extra>',
      marker: {
        color: colors // Assign the array of colors based on aggregated data
      }
    };
  }

  return (
    <div style={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
      <div className="search-container" style={{
        height: "100%",
        padding: "10px",
        width: "calc((100% - 20px) / 2 * 1.95 + 20px)",
        maxWidth: "none"
      }}>
        <h2 style={{ fontSize: "18px", fontWeight: "bold", marginBottom: "15px" }}>Category Coverage</h2>
        <p className="subtitle" style={{ fontSize: "14px", marginTop: "-10px", marginBottom: "20px", color: "#555" }}>
          See how many courses satisfy each requirement category for a specific major and semester.
        </p>
        <div className="search-inputs" style={{ marginBottom: "20px", display: "flex", gap: "20px", alignItems: 'flex-start' /* Align items to top */ }}>
          {/* Major Dropdown Group */}
          <div className="filter-control-group">
            <label className="filter-label">Major</label>
            <div className="select-wrapper">
              <select
                value={selectedMajor}
                onChange={e => {
                  setSelectedMajor(e.target.value);
                  setSemester(''); // Reset semester when major changes
                }}
                className="search-dropdown"
              >
                {Object.entries(majors).map(([code, name]) => (
                  <option key={code} value={code}>{name}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Semester Dropdown Group */}
          <div className="filter-control-group">
            <label className="filter-label">Semester</label>
            <div className="select-wrapper">
              <select
                value={semester}
                onChange={e => setSemester(e.target.value)}
                className="search-dropdown"
              >
                <option value="">All Semesters</option>
                {validSemesters.map(sem => (
                  <option key={sem} value={sem}>{sem}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {loading ? (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '400px',
            width: '100%'
          }}>
            <div className="loading-spinner"></div>
          </div>
        ) : chartData && chartData.coverage ? (
          <div style={{ backgroundColor: "white", padding: "20px", borderRadius: "5px", marginTop: "20px" }}>
            <Plot
              data={[plotTrace]}
              layout={{
                title: `Course Count per Requirement for ${majors[selectedMajor]}${semester ? ` (${semester})` : ''}`,
                xaxis: { title: 'Number of Courses' },
                yaxis: { title: 'Requirement', automargin: true },
                margin: { l: 250, r: 50, t: 50, b: 50 },
                paper_bgcolor: 'white',
                plot_bgcolor: 'white',
                font: {
                  family: 'Arial, sans-serif'
                },
                width: null,  // Allow the plot to be responsive
                height: 600,
                autosize: true
              }}
              style={{ width: "100%", height: "600px" }}
              useResizeHandler={true}  // Enable responsive resizing
              config={{ responsive: true }}  // Enable responsive behavior
            />
          </div>
        ) : (
          <div className="selected-filters">
            <div className="filter-tag" style={{ backgroundColor: '#ff4d4d' }}>
              No data available
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CategoryCoverage;
