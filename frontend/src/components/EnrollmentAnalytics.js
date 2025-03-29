import React, { useState } from 'react';
import Plot from 'react-plotly.js';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

function parseSemester(semesterString) {
  // "S21" => {year: 21, seasonOrder: 1}, etc.
  const seasonChar = semesterString[0];
  const year = parseInt(semesterString.slice(1), 10) || 0;

  let seasonOrder;
  switch (seasonChar) {
    case 'S': // Spring
      seasonOrder = 1;
      break;
    case 'M': // Summer
      seasonOrder = 2;
      break;
    case 'F': // Fall
      seasonOrder = 3;
      break;
    default:
      seasonOrder = 0;
  }
  return { year, seasonOrder };
}

// Aggregated Enrollment Analytics: Multiple courses, aggregated view
const AggregatedEnrollmentAnalytics = () => {
  const [courseInput, setCourseInput] = useState('');
  const [courses, setCourses] = useState([]);

  const removeCourse = (courseCodeToRemove) => {
    setCourses(prev => prev.filter(course => course.courseCode !== courseCodeToRemove));
  };

  const addCourse = () => {
    const courseCode = courseInput.trim();
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

  // Gather all semesters across all courses & sort them
  const getAllSemestersSorted = () => {
    const semesterSet = new Set();
    courses.forEach(({ data }) => {
      if (data) {
        data.forEach(item => {
          semesterSet.add(item.semester);
        });
      }
    });
    const all = Array.from(semesterSet);
    all.sort((s1, s2) => {
      const A = parseSemester(s1);
      const B = parseSemester(s2);
      if (A.year !== B.year) return A.year - B.year;
      return A.seasonOrder - B.seasonOrder;
    });
    return all;
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

    return traces;
  };

  return (
    <div style={{ marginBottom: "40px" }}>
      <h2>Aggregated Enrollment Analytics</h2>
      <div style={{ marginBottom: "20px" }}>
        <input
          type="text"
          value={courseInput}
          onChange={(e) => setCourseInput(e.target.value)}
          placeholder="Enter course code"
          style={{ marginRight: "10px" }}
        />
        <button onClick={addCourse}>Add Course</button>
      </div>

      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '8px',
        marginBottom: "20px"
      }}>
        {courses.map(({ courseCode, loading, error }) => (
          <div
            key={courseCode}
            style={{
              display: 'flex',
              alignItems: 'center',
              backgroundColor: '#E8E8E8',
              borderRadius: '16px',
              padding: '4px 12px',
              fontSize: '14px',
              color: '#333',
              gap: '8px'
            }}
          >
            <span>
              {courseCode} {loading && "(Loading...)"} {error && `(Error: ${error})`}
            </span>
            <button
              onClick={() => removeCourse(courseCode)}
              style={{
                border: 'none',
                background: 'none',
                color: '#666',
                cursor: 'pointer',
                padding: '0',
                fontSize: '16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '20px',
                height: '20px',
                borderRadius: '50%',
                transition: 'background-color 0.2s',
                ':hover': {
                  backgroundColor: '#DDD'
                }
              }}
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <Plot
        data={buildTraces()}
        layout={{
          title: "Aggregated Enrollment Over Semesters",
          xaxis: { title: "Semester" },
          yaxis: { title: "Enrollment Count" }
        }}
        style={{ width: "100%", height: "600px" }}
      />
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

  const loadCourse = () => {
    const code = courseInput.trim();
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
        setCourseData(json.enrollment_data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  };

  const getAllSemestersSorted = () => {
    const semesterSet = new Set();
    if (courseData) {
      courseData.forEach(item => semesterSet.add(item.semester));
    }
    const all = Array.from(semesterSet);
    all.sort((s1, s2) => {
      const A = parseSemester(s1);
      const B = parseSemester(s2);
      if (A.year !== B.year) return A.year - B.year;
      return A.seasonOrder - B.seasonOrder;
    });
    return all;
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

    return traces;
  };

  return (
    <div>
      <h2>Class Enrollment Analytics</h2>
      <div style={{ marginBottom: "20px" }}>
        <input
          type="text"
          value={courseInput}
          onChange={(e) => setCourseInput(e.target.value)}
          placeholder="Enter course code"
          style={{ marginRight: "10px" }}
        />
        <button onClick={loadCourse}>Load Course</button>
      </div>

      <div style={{ marginBottom: "20px" }}>
        {loading && <p>Loading...</p>}
        {error && <p>Error: {error}</p>}
      </div>

      <Plot
        data={buildTraces()}
        layout={{
          title: courseCode ? `Enrollment for ${courseCode}` : "Enrollment Over Semesters",
          xaxis: { title: "Semester" },
          yaxis: { title: "Enrollment Count" }
        }}
        style={{ width: "100%", height: "600px" }}
      />
    </div>
  );
};

const EnrollmentAnalytics = () => {
  return (
    <div style={{ padding: "20px" }}>
      <h1>Enrollment Analytics Dashboard</h1>
      <AggregatedEnrollmentAnalytics />
      <hr style={{ margin: "40px 0" }} />
      <ClassEnrollmentAnalytics />
    </div>
  );
};

export default EnrollmentAnalytics;
