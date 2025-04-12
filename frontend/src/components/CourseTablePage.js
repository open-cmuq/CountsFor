import React, { useState, useEffect, useCallback } from "react";
import "../styles.css";
import SearchBar from "./SearchBar";
import CourseTable from "./CourseTable";
import SelectedFilters from "./SelectedFilters";
import { formatCourseCode } from './utils/courseCodeFormatter';
import { sortSemesters } from './utils/semesterUtils';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const CourseTablePage = () => {
  // States for department and course search input
  const [selectedDepartments, setSelectedDepartments] = useState(() => {
    const saved = localStorage.getItem("selectedDepartments");
    return saved ? JSON.parse(saved) : [];
  });

  const [searchQuery, setSearchQuery] = useState(() => {
    return localStorage.getItem("searchQuery") || "";
  });

  // States for offered-location checkboxes
  const [offeredQatar, setOfferedQatar] = useState(() => {
    const saved = localStorage.getItem("offeredQatar");
    return saved !== null ? JSON.parse(saved) : true;
  });

  const [offeredPitts, setOfferedPitts] = useState(() => {
    const saved = localStorage.getItem("offeredPitts");
    return saved !== null ? JSON.parse(saved) : null;
  });

  // "No Prerequisites" flag: when true, fetch courses with no prerequisites
  const [noPrereqs, setNoPrereqs] = useState(() => {
    const saved = localStorage.getItem("noPrereqs");
    return saved !== null ? JSON.parse(saved) : null;
  });

  // Requirement filters (for BA, BS, CS, IS)
  const [selectedFilters, setSelectedFilters] = useState(() => {
    const saved = localStorage.getItem("selectedFilters");
    return saved ? JSON.parse(saved) : { BA: [], BS: [], CS: [], IS: [] };
  });

  // Offered semester filter (selected via a dropdown in the table header)
  const [selectedOfferedSemesters, setSelectedOfferedSemesters] = useState(() => {
    const saved = localStorage.getItem("selectedOfferedSemesters");
    return saved ? JSON.parse(saved) : [];
  });

  // All available offered semester options (fetched from the dedicated endpoint)
  const [offeredOptions, setOfferedOptions] = useState([]);

  // New state for requirement type filtering
  const [coreOnly, setCoreOnly] = useState(() => {
    const saved = localStorage.getItem("coreOnly");
    return saved !== null ? JSON.parse(saved) : true;
  });

  const [genedOnly, setGenedOnly] = useState(() => {
    const saved = localStorage.getItem("genedOnly");
    return saved !== null ? JSON.parse(saved) : true;
  });

  // For pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [coursesPerPage, setCoursesPerPage] = useState(25);

  // Courses and requirements from API
  const [courses, setCourses] = useState([]);
  const [requirements, setRequirements] = useState({ BA: [], BS: [], CS: [], IS: [] });

  const [compactViewMode, setCompactViewMode] = useState(() => {
    return localStorage.getItem("compactViewMode") || "full";
  });
  const [showConfirmPopup, setShowConfirmPopup] = useState(false);
  const [showClearPopup, setShowClearPopup] = useState(false);
  const [toast, setToast] = useState({ show: false, message: "" });

  // Loading state for the CourseTable
  const [loading, setLoading] = useState(true);

  // Save states to localStorage
  useEffect(() => {
    localStorage.setItem("selectedDepartments", JSON.stringify(selectedDepartments));
    localStorage.setItem("searchQuery", searchQuery);
    localStorage.setItem("offeredQatar", JSON.stringify(offeredQatar));
    localStorage.setItem("offeredPitts", JSON.stringify(offeredPitts));
    localStorage.setItem("noPrereqs", JSON.stringify(noPrereqs));
    localStorage.setItem("selectedFilters", JSON.stringify(selectedFilters));
    localStorage.setItem("selectedOfferedSemesters", JSON.stringify(selectedOfferedSemesters));
    localStorage.setItem("coreOnly", JSON.stringify(coreOnly));
    localStorage.setItem("genedOnly", JSON.stringify(genedOnly));
    localStorage.setItem("compactViewMode", compactViewMode);
  }, [
    selectedDepartments,
    searchQuery,
    offeredQatar,
    offeredPitts,
    noPrereqs,
    selectedFilters,
    selectedOfferedSemesters,
    coreOnly,
    genedOnly,
    compactViewMode
  ]);

  // Pagination logic
  const totalPages = Math.ceil(courses.length / coursesPerPage);
  const indexOfLastCourse = currentPage * coursesPerPage;
  const indexOfFirstCourse = indexOfLastCourse - coursesPerPage;
  const currentCourses = courses.slice(indexOfFirstCourse, indexOfLastCourse);

  // Update current page to the last valid page if the number of courses changes
  useEffect(() => {
    const totalPages = Math.ceil(courses.length / coursesPerPage);
    if (currentPage > totalPages && totalPages > 0) {
      setCurrentPage(totalPages);
    }
  }, [courses, coursesPerPage, currentPage]);

  // Scroll to top when switching pages
  const handlePageChange = (page) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const getPaginationButtons = () => {
    const buttons = [];
    if (totalPages <= 5) {
      for (let i = 1; i <= totalPages; i++) buttons.push(i);
    } else {
      buttons.push(1);
      if (currentPage > 3) buttons.push("...");
      for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++)
        buttons.push(i);
      if (currentPage < totalPages - 2) buttons.push("...");
      buttons.push(totalPages);
    }
    return buttons;
  };

  // Fetch departments from API
  useEffect(() => {
    const fetchDepartments = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/departments`);
        if (!response.ok) throw new Error("Failed to fetch departments");
        const data = await response.json();
        console.log("Fetched departments:", data);
      } catch (error) {
        console.error("Error fetching departments:", error);
      }
    };
    fetchDepartments();
  }, []);

  // Fetch requirements from API
  useEffect(() => {
    const fetchRequirements = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/requirements`);
        if (!response.ok) throw new Error("Failed to fetch requirements");
        const data = await response.json();
        console.log("Requirements fetched:", data);
        const transformedRequirements = { BA: [], BS: [], CS: [], IS: [] };
        data.requirements.forEach(({ requirement, type, major }) => {
          const majorKey = { cs: "CS", is: "IS", ba: "BA", bio: "BS" }[major];
          if (majorKey && transformedRequirements[majorKey]) {
            transformedRequirements[majorKey].push({ requirement, type: !!type, major: majorKey });
          }
        });

        setRequirements(transformedRequirements);
      } catch (error) {
        console.error("Error fetching requirements:", error);
      }
    };
    fetchRequirements();
  }, []);

  // Memoize the helper function so it only changes when coreOnly or genedOnly change.
  const courseMatchesRequirementFilter = useCallback((course) => {
    // If BOTH Core and GenEd are selected (or potentially neither, though UI might prevent),
    // do not filter based on requirement type. Show all courses that pass other filters.
    if ((coreOnly && genedOnly) || (!coreOnly && !genedOnly) ) {
      return true; // Don't filter by type
    }

    // --- Apply filter only if exactly ONE type is selected ---

    if (!course.requirements) {
        return false; // No requirements means it cannot match a specific type filter
    }

    const majors = Object.keys(course.requirements);
    for (const major of majors) {
      if (course.requirements[major]) { // Check if major requirements exist
          for (const reqObj of course.requirements[major]) {
            // reqObj.type is true for GenEd, false for Core
            // If coreOnly is true (and genedOnly must be false here), check for Core type
            if (coreOnly && !reqObj.type) return true;
            // If genedOnly is true (and coreOnly must be false here), check for GenEd type
            if (genedOnly && reqObj.type) return true;
          }
      }
    }

    return false; // No matching requirement type found for the single selected type
  }, [coreOnly, genedOnly]);

  // Fetch courses using combined filters from backend
  useEffect(() => {
    const fetchCourses = async () => {
      setLoading(true);
      try {
        // for multi-select
        const departmentsToFetch = selectedDepartments;

        // If no departments are selected, send one request without the department param
        const queries = departmentsToFetch.length > 0 ? departmentsToFetch : [null];

        const results = await Promise.all(
          queries.map(async (dep) => {
            const params = new URLSearchParams();

            if (dep) params.append("department", dep);
            if (searchQuery) params.append("searchQuery", formatCourseCode(searchQuery));
            if (selectedOfferedSemesters.length > 0)
              params.append("semester", selectedOfferedSemesters.join(","));
            if (noPrereqs === false) params.append("has_prereqs", false);
            else if (noPrereqs === true) params.append("has_prereqs", true);
            if (offeredQatar !== null) params.append("offered_qatar", offeredQatar);
            if (offeredPitts !== null) params.append("offered_pitts", offeredPitts);
            if (selectedFilters.CS.length > 0)
              params.append("cs_requirement", selectedFilters.CS.join(","));
            if (selectedFilters.IS.length > 0)
              params.append("is_requirement", selectedFilters.IS.join(","));
            if (selectedFilters.BA.length > 0)
              params.append("ba_requirement", selectedFilters.BA.join(","));
            if (selectedFilters.BS.length > 0)
              params.append("bs_requirement", selectedFilters.BS.join(","));

            const url = `${API_BASE_URL}/courses/search?${params.toString()}`;
            console.log("Fetching:", url);
            const response = await fetch(url);
            if (!response.ok) return [];

            const data = await response.json();
            return data.courses || [];
          })
        );

        // Flatten and deduplicate
        const allCourses = results.flat();
        const uniqueCourses = Array.from(
          new Map(allCourses.map((c) => [c.course_code, c])).values()
        );

        // Apply additional filtering to enforce AND logic between different major categories
        let filteredCourses = uniqueCourses;

        // Get list of majors with active filters
        const majorsWithFilters = Object.keys(selectedFilters).filter(
          major => selectedFilters[major] && selectedFilters[major].length > 0
        );

        // If multiple major categories have active filters, apply AND logic
        if (majorsWithFilters.length > 1) {
          filteredCourses = uniqueCourses.filter(course => {
            // Check if course fulfills requirements for ALL majors with active filters
            return majorsWithFilters.every(major => {
              const majorRequirements = course.requirements[major] || [];
              // Check if any requirements in this major match the selected filters
              return majorRequirements.some(reqObj =>
                selectedFilters[major].includes(reqObj.requirement)
              );
            });
          });
        }

        // Apply Core/GenEd filter
        filteredCourses = filteredCourses.filter(courseMatchesRequirementFilter);
        setCourses(filteredCourses);
      } catch (error) {
        console.error("Error fetching courses:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchCourses();
  }, [
    selectedDepartments,
    searchQuery,
    selectedOfferedSemesters,
    noPrereqs,
    offeredQatar,
    offeredPitts,
    selectedFilters,
    coreOnly,
    genedOnly,
    courseMatchesRequirementFilter,
  ]);

  // Fetch all semesters from the dedicated endpoint
  useEffect(() => {
    const fetchSemesters = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/courses/semesters`);
        if (!response.ok) throw new Error("Failed to fetch semesters");
        const data = await response.json();
        // Sort semesters by most recent first
        const sortedSemesters = sortSemesters(data.semesters);
        setOfferedOptions(sortedSemesters);
      } catch (error) {
        console.error("Error fetching semesters:", error);
        setOfferedOptions([]);
      }
    };
    fetchSemesters();
  }, []);

  const handleFilterChange = (major, newSelection) => {
    setSelectedFilters((prev) => ({
      ...prev,
      [major]: Array.isArray(newSelection)
        ? newSelection
        : prev[major].filter((filter) => filter !== newSelection),
    }));
  };

  const clearFilters = (major) => {
    setSelectedFilters((prev) => ({ ...prev, [major]: [] }));
  };

  const removeOfferedSemester = (semester) => {
    setSelectedOfferedSemesters((prev) => prev.filter((s) => s !== semester));
  };

  const handleRemoveCourse = (courseCode) => {
    setCourses((prev) => prev.filter((c) => c.course_code !== courseCode));
  };

  const getPlannedCourses = () => {
    const saved = localStorage.getItem("plannedCourses");
    return saved ? JSON.parse(saved) : [];
  };

  const addCoursesToPlan = (newCourses) => {
    const existing = getPlannedCourses();

    // Avoid duplicates
    const uniqueCourses = newCourses.filter(
      (c) => !existing.some((e) => e.course_code === c.course_code)
    );

    const updated = [...existing, ...uniqueCourses];
    localStorage.setItem("plannedCourses", JSON.stringify(updated));

    setToast({
      show: true,
      message: `${uniqueCourses.length} course${uniqueCourses.length !== 1 ? "s" : ""} added to Plan! 🎯`,
    });

    setTimeout(() => setToast({ show: false, message: "" }), 2000);
  };

  const allAlreadyAdded = courses.length > 0 && courses.every((c) =>
    (JSON.parse(localStorage.getItem("plannedCourses")) || []).some(
      (p) => p.course_code === c.course_code
    )
  );

  const clearAllFilters = () => {
    setSelectedDepartments([]);
    setSelectedFilters({ BA: [], BS: [], CS: [], IS: [] });
    setSelectedOfferedSemesters([]);
    setSearchQuery("");
    setOfferedQatar(true);
    setOfferedPitts(null);
    setNoPrereqs(null);
    setCoreOnly(true);
    setGenedOnly(true);
  }

  const hasActiveFilters =
  selectedDepartments.length > 0 ||
  searchQuery.trim() !== "" ||
  selectedFilters.BA.length > 0 ||
  selectedFilters.BS.length > 0 ||
  selectedFilters.CS.length > 0 ||
  selectedFilters.IS.length > 0 ||
  selectedOfferedSemesters.length > 0;


  return (
    <div className="table-container">
      <h1 className="title">CMU-Q General Education</h1>

      <SearchBar
        selectedDepartments={selectedDepartments}
        setSelectedDepartments={setSelectedDepartments}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        noPrereqs={noPrereqs}
        setNoPrereqs={setNoPrereqs}
        offeredQatar={offeredQatar}
        setOfferedQatar={setOfferedQatar}
        offeredPitts={offeredPitts}
        setOfferedPitts={setOfferedPitts}
        coreOnly={coreOnly}
        setCoreOnly={setCoreOnly}
        genedOnly={genedOnly}
        setGenedOnly={setGenedOnly}
      />

      <SelectedFilters
        selectedFilters={selectedFilters}
        handleFilterChange={handleFilterChange}
        selectedOfferedSemesters={selectedOfferedSemesters}
        removeOfferedSemester={removeOfferedSemester}
      />

      {/* Top-left pagination, compact view, clear filter, add courses to plan button*/}
      <div className="view-toolbar">
        <span className="view-count">
          Showing {indexOfFirstCourse + 1} - {Math.min(indexOfLastCourse, courses.length)} of {courses.length}
        </span>

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

      <button
        className={`clear-all-filters-btn ${!hasActiveFilters ? "disabled" : ""}`}
        onClick={() => hasActiveFilters && setShowClearPopup(true)}
        disabled={!hasActiveFilters}
        title={hasActiveFilters ? "Click to reset all filters" : "No filters to clear!"}
      >
        Clear All Filters
      </button>


      {courses.length > 0 && (
        <button
            className={`add-all-btn ${allAlreadyAdded ? "disabled" : ""}`}
            disabled={allAlreadyAdded}
            title={allAlreadyAdded ? "All courses listed already in plan" : "Click to add all courses to plan"}
            onClick={() => {
              if (courses.length > 20) {
                setShowConfirmPopup(true);
              } else {
                addCoursesToPlan(courses);
              }
            }}
          >
            {allAlreadyAdded ? "All Courses in Plan" : "Add All to Plan"}
        </button>
      )}

      </div>

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
          courses={currentCourses}
          allRequirements={requirements}
          selectedFilters={selectedFilters}
          handleFilterChange={handleFilterChange}
          clearFilters={clearFilters}
          offeredOptions={offeredOptions}
          selectedOfferedSemesters={selectedOfferedSemesters}
          setSelectedOfferedSemesters={setSelectedOfferedSemesters}
          coreOnly={coreOnly}
          genedOnly={genedOnly}
          handleRemoveCourse={handleRemoveCourse}
          noPrereqs={noPrereqs}
          setNoPrereqs={setNoPrereqs}
          compactViewMode={compactViewMode}
          allowRemove={false}
        />
      )}

      {toast.show && (
        <div className="toast-snackbar">
          {toast.message}
        </div>
      )}

      {showConfirmPopup && (
        <div className="popup-overlay-2">
          <div className="popup-box">
            <p>
              Are you sure you want to add <strong>{courses.length}</strong> courses to your plan?
            </p>
            <div className="popup-buttons">
              <button
                className="confirm-btn"
                onClick={() => {
                  addCoursesToPlan(courses);
                  setShowConfirmPopup(false);
                }}
              >
                Yes, Add All
              </button>
              <button className="cancel-btn" onClick={() => setShowConfirmPopup(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {showClearPopup && (
        <div className="popup-overlay-2">
          <div className="popup-box">
            <p>
              Are you sure you want to all filters? This will reset all your search and requirement filter selections.
            </p>
            <div className="popup-buttons">
              <button
                className="confirm-btn"
                onClick={() => {
                  clearAllFilters();
                  setShowClearPopup(false);
                }}
              >
                Clear All Filters
              </button>
              <button className="cancel-btn"
              onClick={() => setShowClearPopup(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bottom pagination */}
      <div className="pagination-container">
        <button onClick={() => handlePageChange(Math.max(currentPage - 1, 1))} disabled={currentPage === 1}>‹</button>
        {getPaginationButtons().map((num, idx) => (
          <button
            key={idx}
            onClick={() => typeof num === "number" && handlePageChange(num)}
            className={num === currentPage ? "active" : ""}
            disabled={num === "..."}
          >
            {num}
          </button>
        ))}
        <button onClick={() => handlePageChange(Math.min(currentPage + 1, totalPages))} disabled={currentPage === totalPages}>›</button>

        <select value={coursesPerPage} onChange={(e) => { setCoursesPerPage(parseInt(e.target.value)); setCurrentPage(1); }}>
          {[10, 25, 50, 100].map(size => <option key={size} value={size}>{size}</option>)}
        </select>
      </div>


    </div>
  );
};

export default CourseTablePage;
