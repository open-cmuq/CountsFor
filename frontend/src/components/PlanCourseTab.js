import React, { useState, useEffect } from "react";
import CourseTable from "./CourseTable";
import "../styles.css";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const PlanCourseTab = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [addedCourses, setAddedCourses] = useState([]);
  const [requirements, setRequirements] = useState({ BA: [], BS: [], CS: [], IS: [] });

  useEffect(() => {
    const fetchRequirements = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/requirements`);
        const data = await response.json();
        const grouped = { BA: [], BS: [], CS: [], IS: [] };
        data.requirements.forEach(({ requirement, major }) => {
          const majorKey = {
            cs: "CS",
            is: "IS",
            ba: "BA",
            bio: "BS",
          }[major];
          if (majorKey) grouped[majorKey].push({ requirement });
        });
        setRequirements(grouped);
      } catch (err) {
        console.error("Failed to fetch requirements:", err);
      }
    };
    fetchRequirements();
  }, []);

  const handleSearch = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/courses/search?searchQuery=${searchQuery}`);
      const data = await response.json();
      setSearchResults(data.courses || []);
    } catch (err) {
      console.error("Search error:", err);
    }
  };

  const addCourse = async (course) => {
    if (addedCourses.some((c) => c.course_code === course.course_code)) return;
    try {
      const res = await fetch(`${API_BASE_URL}/courses/${course.course_code}`);
      const fullCourse = await res.json();
      setAddedCourses((prev) => [...prev, fullCourse]);
      setSearchQuery("");
      setSearchResults([]);
    } catch (err) {
      console.error("Error adding course:", err);
    }
  };

  const removeCourse = (code) => {
    setAddedCourses((prev) => prev.filter((c) => c.course_code !== code));
  };

  return (
    <div className="plan-tab">
      <h1 className="title">Plan Courses</h1>

      <div className="search-bar">
        <input
          className="search-input"
          type="text"
          placeholder="Search by course code"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button className="search-btn" onClick={handleSearch}>🔍</button>
      </div>

      {searchResults.length > 0 && (
        <div className="search-results">
        <ul className="search-result-list">
        {searchResults.map((course) => (
            <li key={course.course_code} className="search-result-item">
            <span
                className="course-link"
                onClick={() => addCourse(course)}
                title="Click to add"
            >
                {course.course_code} – {course.course_name}
            </span>
            <button className="add-btn" onClick={() => addCourse(course)}>Add</button>
            </li>
        ))}
        </ul>
        </div>
      )}

      <CourseTable
        courses={addedCourses}
        allRequirements={requirements}
        selectedFilters={{ BA: [], BS: [], CS: [], IS: [] }}
        handleFilterChange={() => {}}
        clearFilters={() => {}}
        offeredOptions={[]}
        selectedOfferedSemesters={[]}
        setSelectedOfferedSemesters={() => {}}
        coreOnly={false}
        genedOnly={false}
        allowRemove={true}
        onRemoveCourse={removeCourse}
      />
    </div>
  );
};

export default PlanCourseTab;
