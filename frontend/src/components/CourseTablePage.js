import React, { useState, useEffect } from "react";
import mockCourses from "../mockData/courses";
import "../styles.css";
import SearchBar from "./SearchBar";
import CourseTable from "./CourseTable";
import SelectedFilters from "./SelectedFilters";

const API_BASE_URL = "http://127.0.0.1:8000";

const CourseTableMock = () => {
  const [requirements, setRequirements] = useState({
    BA: [],
    BS: [],
    CS: [],
    IS: [],
  });

  // Fetch requirements from FastAPI instead of using mock data
  useEffect(() => {
    const fetchRequirements = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/requirements`);
        if (!response.ok) throw new Error("Failed to fetch requirements");
        const data = await response.json();
        console.log("Fetched Requirements from API:", data); // Debugging Step
        setRequirements(data);
      } catch (error) {
        console.error("Error fetching requirements:", error);
      }
    };

    fetchRequirements();
  }, []);


  const [selectedFilters, setSelectedFilters] = useState({
    BA: [],
    BS: [],
    CS: [],
    IS: [],
  });

  const [visibleCourses, setVisibleCourses] = useState(mockCourses);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDepartment, setSelectedDepartment] = useState("");

  const departments = ["History", "Computer Science", "Biology", "Business"];

  const handleFilterChange = (major, newSelection) => {
    setSelectedFilters((prev) => ({
      ...prev,
      [major]: Array.isArray(newSelection) ? newSelection : prev[major].filter((filter) => filter !== newSelection),
    }));
  };

  const clearFilters = (major) => {
    setSelectedFilters((prev) => ({ ...prev, [major]: [] }));
  };

  const filteredCourses = visibleCourses.filter((course) =>
    (selectedDepartment === "" || course.department === selectedDepartment) &&
    (searchQuery === "" || course.course_code.includes(searchQuery)) &&
    Object.keys(selectedFilters).every((major) => {
      if (selectedFilters[major].length === 0) return true;

      const courseReqs = course.requirements?.[major] || [];

      return selectedFilters[major].some((req) =>
        courseReqs.map((r) => r.toLowerCase()).includes(String(req).toLowerCase())
      );
    })
  );

  return (
    <div className="table-container">
      <h1 className="title">CMU-Q General Education</h1>

      <SearchBar
        departments={departments}
        selectedDepartment={selectedDepartment}
        setSelectedDepartment={setSelectedDepartment}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
      />
      <SelectedFilters selectedFilters={selectedFilters} handleFilterChange={handleFilterChange} />
      <CourseTable
        courses={filteredCourses}
        allRequirements={requirements} // Now using real API data
        selectedFilters={selectedFilters}
        handleFilterChange={handleFilterChange}
        clearFilters={clearFilters}
        setVisibleCourses={setVisibleCourses}
      />
    </div>
  );
};

export default CourseTableMock;
