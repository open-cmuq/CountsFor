import React, { useState, useEffect, useCallback } from 'react';
import Plot from 'react-plotly.js';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const CategoryCoverage = ({ selectedMajor, semester, majors }) => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append("major", selectedMajor);
      if (semester.trim()) {
        params.append("semester", semester.trim());
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
      hovertemplate: 'Count: %{x}<extra></extra>'
    };
  }

  return (
    <div>
      {loading ? (
        <p>Loading analytics data...</p>
      ) : chartData && chartData.coverage ? (
        <Plot
          data={[plotTrace]}
          layout={{
            title: `Course Count per Requirement for ${majors[selectedMajor]}${semester ? ` (${semester})` : ''}`,
            xaxis: { title: 'Number of Courses' },
            yaxis: { title: 'Requirement' },
            margin: { l: 150, r: 50, t: 50, b: 50 }
          }}
          style={{ width: "100%", height: "600px" }}
        />
      ) : (
        <p>No data available.</p>
      )}
    </div>
  );
};

export default CategoryCoverage;
