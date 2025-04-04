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
    // Sort the coverage data by course count (ascending)
    const sortedCoverage = [...chartData.coverage].sort((a, b) => a.num_courses - b.num_courses);
    const xData = sortedCoverage.map(item => item.num_courses);
    const yData = sortedCoverage.map(item => {
      // Extract a shorter requirement label (the text after the last '---')
      const parts = item.requirement.split('---');
      return parts[parts.length - 1].trim();
    });
    plotTrace = {
      x: xData,
      y: yData,
      type: 'bar',
      orientation: 'h',
      hovertemplate: 'Count: %{x}<extra></extra>',
      marker: {
        color: '#4A68FB'  // Using the same blue as other components
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
        <div className="search-inputs" style={{ marginBottom: "20px", display: "flex", gap: "20px" }}>
          <label className="search-label">
            Major:&nbsp;
            <select
              value={selectedMajor}
              onChange={e => {
                setSelectedMajor(e.target.value);
                setSemester(''); // Reset semester when major changes
              }}
              className="search-dropdown"
              style={{
                padding: "8px",
                borderRadius: "4px",
                border: "1px solid #ccc",
                minWidth: "200px"
              }}
            >
              {Object.entries(majors).map(([code, name]) => (
                <option key={code} value={code}>{name}</option>
              ))}
            </select>
          </label>

          <label className="search-label">
            Semester:&nbsp;
            <select
              value={semester}
              onChange={e => setSemester(e.target.value)}
              className="search-dropdown"
              style={{
                padding: "8px",
                borderRadius: "4px",
                border: "1px solid #ccc",
                minWidth: "120px"
              }}
            >
              <option value="">All Semesters</option>
              {validSemesters.map(sem => (
                <option key={sem} value={sem}>{sem}</option>
              ))}
            </select>
          </label>
        </div>

        {loading ? (
          <div className="selected-filters">
            <div className="filter-tag" style={{ backgroundColor: '#4A68FB' }}>
              Loading analytics data...
            </div>
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
