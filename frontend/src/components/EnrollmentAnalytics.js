import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { sortSemestersChronologically } from './utils/semesterUtils';
import "../styles.css";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const formatCourseCode = (code) => {
  // Remove all spaces and convert to uppercase
  code = code.replace(/\s+/g, '').toUpperCase();

  // If the code is just numbers or already has a dash, return it
  if (/^\d+$/.test(code)) {
    // Add dash between department number and course number
    return code.replace(/^(\d{2})(\d{3})$/, '$1-$2');
  }

  // If it already has a dash, return as is
  if (code.includes('-')) {
    return code;
  }

  return code;
};

// Aggregated Enrollment Analytics: Multiple courses, aggregated view
const AggregatedEnrollmentAnalytics = () => {
  const [courseInput, setCourseInput] = useState('');
  const [courses, setCourses] = useState([]);
  const [initialLoading, setInitialLoading] = useState(true);

  // Set initial loading to false after a short delay to simulate data loading
  useEffect(() => {
    const timer = setTimeout(() => {
      setInitialLoading(false);
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  const removeCourse = (courseCodeToRemove) => {
    setCourses(prev => prev.filter(course => course.courseCode !== courseCodeToRemove));
  };

  const addCourse = () => {
    const courseCode = formatCourseCode(courseInput.trim());
    if (!courseCode) return;

    // Prevent duplicates
    if (courses.some(course => course.courseCode === courseCode)) {
      setCourseInput('');
      return;
    }

    setCourses(prev => [...prev, { courseCode, data: null, loading: true, error: null }]);
    setCourseInput('');

    fetch(`${API_BASE_URL}/analytics/enrollment-data?course_code=${courseCode}`)
      .then(response => {
        if (!response.ok) {
          throw new Error("Failed to fetch enrollment data");
        }
        return response.json();
      })
      .then(json => {
        console.log('API Response (Aggregated):', json);
        setCourses(prev =>
          prev.map(course =>
            course.courseCode === courseCode
              ? { ...course, data: json.enrollment_data, loading: false }
              : course
          )
        );
      })
      .catch(error => {
        setCourses(prev =>
          prev.map(course =>
            course.courseCode === courseCode
              ? { ...course, error: error.message, loading: false }
              : course
          )
        );
      });
  };

  // Handle Enter key press for adding a course
  const handleKeyDownAggregated = (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      addCourse();
      // We might not want to blur here if the user intends to add multiple courses quickly
      // event.target.blur();
    }
  };

  // Gather all semesters across all courses & sort them chronologically
  const getAllSemestersSorted = () => {
    const semesterSet = new Set();
    courses.forEach(({ data }) => {
      if (data) {
        data.forEach(item => {
          semesterSet.add(item.semester);
        });
      }
    });
    return sortSemestersChronologically(Array.from(semesterSet));
  };

  // Build traces: aggregate enrollment counts across classes per semester
  const buildTraces = () => {
    const allSemesters = getAllSemestersSorted();
    const traces = [];

    courses.forEach(({ courseCode, data }) => {
      if (!data) return;

      const agg = {};
      data.forEach(item => {
        if (!agg[item.semester]) agg[item.semester] = 0;
        agg[item.semester] += item.enrollment_count;
      });

      const y = allSemesters.map(sem => (agg[sem] !== undefined ? agg[sem] : 0));

      traces.push({
        x: allSemesters,
        y,
        mode: 'lines+markers',
        name: courseCode
      });
    });

    console.log('Traces for Aggregated Plot:', traces);

    return traces;
  };

  return (
    <div className="search-container" style={{ height: "100%", padding: "10px", width: "95%" }}>
      <h2 style={{ fontSize: "18px", fontWeight: "bold", marginBottom: "15px" }}>Enrollment Analytics Across Courses</h2>
      <div className="search-inputs" style={{ marginBottom: "15px", display: "flex", gap: "10px" }}>
        <input
          type="text"
          value={courseInput}
          onChange={(e) => setCourseInput(e.target.value)}
          onKeyDown={handleKeyDownAggregated}
          placeholder="Enter course code"
          className="text-input"
          style={{ width: "200px" }}
        />
        <button
          onClick={addCourse}
          className="add-all-btn"
          style={{
            backgroundColor: "black",
            color: "white",
            padding: "9px 16px",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
            transition: "all 0.3s ease, color 0.3s ease"
          }}
        >
          Add Course
        </button>
      </div>

      <div className="selected-filters" style={{ marginBottom: "15px", minHeight: "30px" }}>
        {courses.map(({ courseCode, loading, error }) => (
          <div
            key={courseCode}
            className="filter-tag"
            style={{
              backgroundColor: error ? '#ff4d4d' : '#4A68FB',
              margin: '2px',
              padding: '5px 10px'
            }}
          >
            <span>
              {courseCode} {loading && "(Loading...)"} {error && `(Error: ${error})`}
            </span>
            <button onClick={() => removeCourse(courseCode)}><b>×</b></button>
          </div>
        ))}
      </div>

      <div style={{ backgroundColor: "white", padding: "10px", borderRadius: "5px", marginTop: "10px" }}>
        {initialLoading ? (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '400px',
            width: '100%'
          }}>
            <div className="loading-spinner"></div>
          </div>
        ) : (
          <Plot
            data={buildTraces()}
            layout={{
              title: "Aggregated Enrollment Over Semesters",
              xaxis: { title: "Semester" },
              yaxis: { title: "Enrollment Count" },
              paper_bgcolor: 'white',
              plot_bgcolor: 'white',
              font: { family: 'Arial, sans-serif' },
              width: null,
              height: 400,
              autosize: true,
              margin: { l: 35, r: 15, t: 40, b: 40 }
            }}
            style={{ width: "100%", height: "400px", marginBottom: "0" }}
            useResizeHandler={true}
            config={{ responsive: true, displayModeBar: true }}
          />
        )}
      </div>
    </div>
  );
};

// Class Enrollment Analytics: Single course with lines per class (excluding Class 0)
const ClassEnrollmentAnalytics = () => {
  const [courseInput, setCourseInput] = useState('');
  const [courseData, setCourseData] = useState(null);
  const [courseCode, setCourseCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [initialLoading, setInitialLoading] = useState(true);

  // Set initial loading to false after a short delay to simulate data loading
  useEffect(() => {
    const timer = setTimeout(() => {
      setInitialLoading(false);
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  const loadCourse = () => {
    const code = formatCourseCode(courseInput.trim());
    if (!code) return;

    setCourseCode(code);
    setLoading(true);
    setError(null);
    setCourseData(null);

    fetch(`${API_BASE_URL}/analytics/enrollment-data?course_code=${code}`)
      .then(response => {
        if (!response.ok) {
          throw new Error("Failed to fetch enrollment data");
        }
        return response.json();
      })
      .then(json => {
        console.log('API Response (Class):', json);
        setCourseData(json.enrollment_data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  };

  // Handle Enter key press for loading a course
  const handleKeyDownClass = (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      loadCourse();
      event.target.blur(); // Blur after loading seems appropriate
    }
  };

  const getAllSemestersSorted = () => {
    const semesterSet = new Set();
    if (courseData) {
      courseData.forEach(item => semesterSet.add(item.semester));
    }
    return sortSemestersChronologically(Array.from(semesterSet));
  };

  // Mapping for class labels
  const classLabels = {
    "1": "First Years",
    "2": "Sophomores",
    "3": "Juniors",
    "4": "Seniors"
  };

  const buildTraces = () => {
    if (!courseData) return [];
    const allSemesters = getAllSemestersSorted();
    const traces = [];

    // Group enrollment data by class, filtering out class "0"
    const byClass = {};
    courseData.forEach(item => {
      // Only include classes 1-4
      if (item.class_ === 0 || item.class_ === "0") return;
      const classKey = String(item.class_);
      if (!byClass[classKey]) byClass[classKey] = [];
      byClass[classKey].push(item);
    });

    Object.entries(byClass).forEach(([classKey, items]) => {
      // Sum enrollment counts if there are multiple rows per semester
      const lookup = {};
      items.forEach(item => {
        if (!lookup[item.semester]) lookup[item.semester] = 0;
        lookup[item.semester] += item.enrollment_count;
      });

      const y = allSemesters.map(sem => (lookup[sem] !== undefined ? lookup[sem] : null));

      // Map the classKey to its corresponding label
      const label = classLabels[classKey] || `Class ${classKey}`;

      traces.push({
        x: allSemesters,
        y,
        mode: 'lines+markers',
        name: `${courseCode} - ${label}`,
        connectgaps: true
      });
    });

    console.log('Traces for Class Plot:', traces);

    return traces;
  };

  return (
    <div className="search-container" style={{ height: "100%", padding: "10px", width: "95%" }}>
      <h2 style={{ fontSize: "18px", fontWeight: "bold", marginBottom: "15px" }}>Enrollment Analytics Across Classes</h2>
      <div className="search-inputs" style={{ marginBottom: "15px", display: "flex", gap: "10px" }}>
        <input
          type="text"
          value={courseInput}
          onChange={(e) => setCourseInput(e.target.value)}
          onKeyDown={handleKeyDownClass}
          placeholder="Enter course code"
          className="text-input"
          style={{ width: "200px" }}
        />
        <button
          onClick={loadCourse}
          className="add-all-btn"
          style={{
            backgroundColor: "black",
            color: "white",
            padding: "9px 16px",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
            transition: "all 0.3s ease, color 0.3s ease"
          }}
        >
          Load Course
        </button>
      </div>

      <div className="selected-filters" style={{ marginBottom: "15px", minHeight: "30px" }}>
        {(loading || error) && (
          <>
            {loading && (
              <div className="filter-tag" style={{ backgroundColor: '#4A68FB', padding: '5px 10px', margin: '2px' }}>
                Loading...
              </div>
            )}
            {error && (
              <div className="filter-tag" style={{ backgroundColor: '#ff4d4d', padding: '5px 10px', margin: '2px' }}>
                Error: {error}
              </div>
            )}
          </>
        )}
      </div>

      <div style={{ backgroundColor: "white", padding: "10px", borderRadius: "5px", marginTop: "10px" }}>
        {initialLoading || loading ? (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '400px',
            width: '100%'
          }}>
            <div className="loading-spinner"></div>
          </div>
        ) : (
          <Plot
            data={buildTraces()}
            layout={{
              title: courseCode ? `Enrollment for ${courseCode}` : "Enrollment Over Semesters",
              xaxis: { title: "Semester" },
              yaxis: { title: "Enrollment Count" },
              paper_bgcolor: 'white',
              plot_bgcolor: 'white',
              font: { family: 'Arial, sans-serif' },
              width: null,
              height: 400,
              autosize: true,
              margin: { l: 35, r: 15, t: 40, b: 40 }
            }}
            style={{ width: "100%", height: "400px", marginBottom: "0" }}
            useResizeHandler={true}
            config={{ responsive: true, displayModeBar: true }}
          />
        )}
      </div>
    </div>
  );
};

const EnrollmentAnalytics = () => {
  return (
    <div style={{
      display: 'flex',
      gap: '20px',
      width: '100%',
      margin: '0',
      padding: '0'
    }}>
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center'
      }}>
        <AggregatedEnrollmentAnalytics />
      </div>
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center'
      }}>
        <ClassEnrollmentAnalytics />
      </div>
    </div>
  );
};

export default EnrollmentAnalytics;
