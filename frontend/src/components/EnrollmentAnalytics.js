import React, { useState, useEffect } from 'react';
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

const EnrollmentAnalytics = () => {
  const [courseInput, setCourseInput] = useState('');
  const [courses, setCourses] = useState([]);
  const [separateLines, setSeparateLines] = useState(false);

  // Add a new course
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
    // Sort using parseSemester
    all.sort((s1, s2) => {
      const A = parseSemester(s1);
      const B = parseSemester(s2);
      if (A.year !== B.year) return A.year - B.year;
      return A.seasonOrder - B.seasonOrder;
    });
    return all;
  };

  // Build the Plotly traces, ensuring all traces share the same x-array
  const buildTraces = () => {
    const allSemesters = getAllSemestersSorted();
    const traces = [];

    courses.forEach(({ courseCode, data }) => {
      if (!data) return;

      if (separateLines) {
        // Separate lines by class
        const byClass = {};
        data.forEach(item => {
          if (!byClass[item.class_]) byClass[item.class_] = [];
          byClass[item.class_].push(item);
        });

        // For each class group, create a y-array that matches allSemesters
        Object.entries(byClass).forEach(([classKey, items]) => {
          // Create a quick lookup from semester => enrollment_count
          // If multiple rows share the same semester+class, sum them or just pick one
          const lookup = {};
          items.forEach(item => {
            if (!lookup[item.semester]) lookup[item.semester] = 0;
            lookup[item.semester] += item.enrollment_count;
          });

          // Build y-array in the correct order
          const y = allSemesters.map(sem => (lookup[sem] !== undefined ? lookup[sem] : null));

          traces.push({
            x: allSemesters,
            y,
            mode: 'lines+markers',
            name: `${courseCode} - Class ${classKey}`,
            connectgaps: true
          });
        });
      } else {
        // Aggregate enrollment counts across classes per semester
        const agg = {};
        data.forEach(item => {
          if (!agg[item.semester]) agg[item.semester] = 0;
          agg[item.semester] += item.enrollment_count;
        });

        // Build y-array
        const y = allSemesters.map(sem => (agg[sem] !== undefined ? agg[sem] : 0));

        traces.push({
          x: allSemesters,
          y,
          mode: 'lines+markers',
          name: courseCode
        });
      }
    });

    return traces;
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>Enrollment Analytics</h1>
      <div style={{ marginBottom: "20px" }}>
        <input
          type="text"
          value={courseInput}
          onChange={(e) => setCourseInput(e.target.value)}
          placeholder="Enter course code"
          style={{ marginRight: "10px" }}
        />
        <button onClick={addCourse}>Add Course</button>
        <label style={{ marginLeft: "20px" }}>
          <input
            type="checkbox"
            checked={separateLines}
            onChange={(e) => setSeparateLines(e.target.checked)}
          />
          Separate lines by class
        </label>
      </div>

      <div style={{ marginBottom: "20px" }}>
        {courses.map(({ courseCode, loading, error }) => (
          <div key={courseCode}>
            {courseCode} {loading && "(Loading...)"} {error && `(Error: ${error})`}
          </div>
        ))}
      </div>

      <Plot
        data={buildTraces()}
        layout={{
          title: "Enrollment Over Semesters",
          xaxis: { title: "Semester" },
          yaxis: { title: "Enrollment Count" }
        }}
        style={{ width: "100%", height: "600px" }}
      />
    </div>
  );
};

export default EnrollmentAnalytics;
