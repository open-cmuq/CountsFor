import React, { useState, useEffect, useRef } from "react";
import CourseTable from "./CourseTable";
import { formatCourseCode } from './utils/courseCodeFormatter';
import "../styles.css";
import "../planTabStyles.css";


const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const PlanCourseTab = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [toast, setToast] = useState({ show: false, message: "" });
  const [showSearchResults, setShowSearchResults] = useState(false);
  const searchRef = useRef(null);
  const [compactViewMode, setCompactViewMode] = useState("full");
  const [loading, setLoading] = useState(true);

  // Use localStorage to persist added courses
  const [addedCourses, setAddedCourses] = useState(() => {
    const savedCourses = localStorage.getItem("plannedCourses");
    return savedCourses ? JSON.parse(savedCourses) : [];
  });

  const [requirements, setRequirements] = useState({ BA: [], BS: [], CS: [], IS: [] });

  // Save added courses to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem("plannedCourses", JSON.stringify(addedCourses));
  }, [addedCourses]);

  useEffect(() => {
    const fetchRequirements = async () => {
      setLoading(true);
      try {
        const response = await fetch(`${API_BASE_URL}/requirements`);
        const data = await response.json();
        const grouped = { BA: [], BS: [], CS: [], IS: [] };
        data.requirements.forEach(({ requirement, type, major }) => {
          const majorKey = {
            cs: "CS",
            is: "IS",
            ba: "BA",
            bio: "BS",
          }[major];
          if (majorKey) grouped[majorKey].push({ requirement, type: !!type, major: majorKey });
        });
        setRequirements(grouped);
      } catch (err) {
        console.error("Failed to fetch requirements:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchRequirements();
  }, []);

  const handleSearch = async () => {
    try {
      const formattedQuery = formatCourseCode(searchQuery);
      const response = await fetch(`${API_BASE_URL}/courses/search?searchQuery=${formattedQuery}`);
      const data = await response.json();
      setSearchResults(data.courses || []);
      setShowSearchResults(true);
    } catch (err) {
      console.error("Search error:", err);
    }
  };

  const addCourse = async (course) => {
    if (addedCourses.some((c) => c.course_code === course.course_code)) {
      setToast({ show: true, message: "Course already added! 😅" });
      setTimeout(() => setToast({ show: false, message: "" }), 3000);
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/courses/${course.course_code}`);
      const fullCourse = await res.json();

      setAddedCourses((prev) => [...prev, fullCourse]);

      setToast({ show: true, message: "Course added! 🎉" });
      setTimeout(() => setToast({ show: false, message: "" }), 3000);
    } catch (err) {
      console.error("Error adding course:", err);
    }
  };

  const removeCourse = (code) => {
    setAddedCourses((prev) => prev.filter((c) => c.course_code !== code));
  };

  const clearAllCourses = () => {
    if (window.confirm("Are you sure you want to clear all planned courses?")) {
      setAddedCourses([]);
    }
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowSearchResults(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);


  return (
    <div className="plan-tab">
      <h1 className="title">Plan Courses</h1>

      <div className="search-container">
        <div className="search-bar-enhanced">
        <input
            className="search-input"
            type="text"
            placeholder="Search by course code (e.g. 15122 or 15-122)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSearch();
            }}
          />
          <button className="search-btn" onClick={handleSearch}>🔍</button>
        </div>

        {showSearchResults && (
          <div className="scrollable-results" ref={searchRef}>
            <div className="results-header-row">
              <h3 className="results-header">
                {searchResults.length > 0
                  ? `${searchResults.length} result${searchResults.length === 1 ? "" : "s"}`
                  : "No courses found for this search!"}
              </h3>
              <button className="close-btn" onClick={() => setShowSearchResults(false)}>✖</button>
            </div>

          {searchResults.map((course) => {
            const isAlreadyAdded = addedCourses.some((c) => c.course_code === course.course_code);
            return (
              <div key={course.course_code} className="course-result-item">
                <div>
                  <b>{course.course_code}</b> – {course.course_name}
                </div>
                <button
                  className={`add-btn ${isAlreadyAdded ? "disabled animated-fade" : ""}`}
                  onClick={() => {
                    if (isAlreadyAdded) {
                      setToast({ show: true, message: "Course already added! 😅" });
                    } else {
                      addCourse(course);
                    }
                    setTimeout(() => setToast({ show: false, message: "" }), 2000);
                  }}
                  title={isAlreadyAdded ? "Already added" : "Click to add"}
                >
                  {isAlreadyAdded ? "Added" : "+ Add"}
                </button>
              </div>
            );
          })}
          </div>
        )}

      </div>


      {addedCourses.length > 0 && (
        <div className="planned-courses-header">
          <div className="selected-title-wrapper">
            Total Courses in Plan: {addedCourses.length}
          </div>

          <select
            className="view-toggle"
            value={compactViewMode}
            onChange={(e) => setCompactViewMode(e.target.value)}
            style={{ margin: "6px", padding: "5px" }}
          >
            <option value="full">Full View</option>
            <option value="last2">Compact (Last 2)</option>
            <option value="last1">Most Compact (Last 1)</option>
          </select>

          <button className="clear-all-btn" onClick={clearAllCourses}>Clear All</button>
        </div>
      )}

      {toast.show && (
        <div className="toast-snackbar">
          {toast.message}
        </div>
      )}


      {loading ? (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '400px',
          width: '100%',
          marginTop: '20px'
        }}>
          <div className="loading-spinner"></div>
        </div>
      ) : (
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
          handleRemoveCourse={removeCourse}
          hideDropdowns={true}
          compactViewMode={compactViewMode}
          isPlanTab={true}
          />
      )}
    </div>


  );



};

export default PlanCourseTab;
