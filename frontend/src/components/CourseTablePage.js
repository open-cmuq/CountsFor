import React, { useState, useEffect } from "react";
import "../styles.css";
import SearchBar from "./SearchBar";
import CourseTable from "./CourseTable";
import SelectedFilters from "./SelectedFilters";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:8000";

const CourseTablePage = () => {
  // States for department and course search input
  const [selectedDepartment, setSelectedDepartment] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  // States for offered-location checkboxes
  const [offeredQatar, setOfferedQatar] = useState(null);
  const [offeredPitts, setOfferedPitts] = useState(null);
  // "No Prerequisites" flag: when true, fetch courses with no prerequisites
  const [noPrereqs, setNoPrereqs] = useState(null);
  // Requirement filters (for BA, BS, CS, IS)
  const [selectedFilters, setSelectedFilters] = useState({ BA: [], BS: [], CS: [], IS: [] });
  // Offered semester filter (selected via a dropdown in the table header)
  const [selectedOfferedSemesters, setSelectedOfferedSemesters] = useState([]);
  // Courses and requirements from API
  const [courses, setCourses] = useState([]);
  const [requirements, setRequirements] = useState({ BA: [], BS: [], CS: [], IS: [] });
  // All available offered semester options (derived from the fetched courses)
  const [offeredOptions, setOfferedOptions] = useState([]);

  // Fetch departments from API
  useEffect(() => {
    const fetchDepartments = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/departments`);
        if (!response.ok) throw new Error("Failed to fetch departments");
        const data = await response.json();
        console.log("Fetched departments:", data);
        // We only need the department list here
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
        data.requirements.forEach(({ requirement, major }) => {
          const majorKey = {
            cs: "CS",
            is: "IS",
            ba: "BA",
            bio: "BS",
          }[major];
          if (majorKey && transformedRequirements[majorKey]) {
            transformedRequirements[majorKey].push(requirement);
          }
        });
        setRequirements(transformedRequirements);
      } catch (error) {
        console.error("Error fetching requirements:", error);
      }
    };

    fetchRequirements();
  }, []);

  // Fetch courses using combined filters from backend
  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const params = new URLSearchParams();
        if (selectedDepartment) params.append("department", selectedDepartment);
        if (searchQuery) params.append("searchQuery", searchQuery);
        if (selectedOfferedSemesters.length > 0)
          params.append("semester", selectedOfferedSemesters.join(","));
        // When "No Prerequisites" is checked, send has_prereqs=false.
        if (noPrereqs === true) params.append("has_prereqs", false);
        // Offered location checkboxes:
        if (offeredQatar !== null) params.append("offered_qatar", offeredQatar);
        if (offeredPitts !== null) params.append("offered_pitts", offeredPitts);

        // For requirement filters:
        if (selectedFilters.CS.length > 0)
          params.append("cs_requirement", selectedFilters.CS.join(","));
        if (selectedFilters.IS.length > 0)
          params.append("is_requirement", selectedFilters.IS.join(","));
        if (selectedFilters.BA.length > 0)
          params.append("ba_requirement", selectedFilters.BA.join(","));
        if (selectedFilters.BS.length > 0)
          params.append("bs_requirement", selectedFilters.BS.join(","));

        const response = await fetch(`${API_BASE_URL}/courses/search?${params.toString()}`);
        if (!response.ok) throw new Error("Failed to fetch courses");
        const data = await response.json();
        setCourses(data.courses);

        // Derive offered options from the returned courses (union of all offered semesters)
        const allSemesters = new Set();
        data.courses.forEach(course => {
          if (course.offered && Array.isArray(course.offered)) {
            course.offered.forEach(sem => allSemesters.add(sem));
          }
        });
        setOfferedOptions(Array.from(allSemesters));
      } catch (error) {
        console.error("Error fetching courses:", error);
      }
    };

    fetchCourses();
  }, [selectedDepartment, searchQuery, selectedOfferedSemesters, noPrereqs, offeredQatar, offeredPitts, selectedFilters]);

  // Update requirement filters (for CS, IS, BA, BS)
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

  // Handler to remove a selected offered semester from filter tags
  const removeOfferedSemester = (semester) => {
    setSelectedOfferedSemesters((prev) => prev.filter((s) => s !== semester));
  };

  return (
    <div className="table-container">
      <h1 className="title">CMU-Q General Education</h1>
      <SearchBar
        selectedDepartment={selectedDepartment}
        setSelectedDepartment={setSelectedDepartment}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        noPrereqs={noPrereqs}
        setNoPrereqs={setNoPrereqs}
        offeredQatar={offeredQatar}
        setOfferedQatar={setOfferedQatar}
        offeredPitts={offeredPitts}
        setOfferedPitts={setOfferedPitts}
      />
      <SelectedFilters
        selectedFilters={selectedFilters}
        handleFilterChange={handleFilterChange}
        selectedOfferedSemesters={selectedOfferedSemesters}
        removeOfferedSemester={removeOfferedSemester}
      />
       <div className="course-count">
        Showing {courses.length} courses
      </div>
      <CourseTable
        courses={courses}
        allRequirements={requirements}
        selectedFilters={selectedFilters}
        handleFilterChange={handleFilterChange}
        clearFilters={clearFilters}
        offeredOptions={offeredOptions}
        selectedOfferedSemesters={selectedOfferedSemesters}
        setSelectedOfferedSemesters={setSelectedOfferedSemesters}
      />
    </div>
  );
};

export default CourseTablePage;
