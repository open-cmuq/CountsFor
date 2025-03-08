import React, { useState, useEffect } from "react";
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

  const [courses, setCourses] = useState([]);  // Store fetched courses

  useEffect(() => {
    const fetchRequirements = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/requirements`);
        if (!response.ok) throw new Error("Failed to fetch requirements");
        const data = await response.json();
        console.log("Fetched Requirements from API:", data);
        setRequirements(data);
      } catch (error) {
        console.error("Error fetching requirements:", error);
      }
    };

    fetchRequirements();
  }, []);

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/courses`);
        if (!response.ok) throw new Error("Failed to fetch courses");
        const data = await response.json();
        console.log("Fetched Courses from API:", data);
        setCourses(data.courses);  // Extract courses list
      } catch (error) {
        console.error("Error fetching courses:", error);
      }
    };

    fetchCourses();
  }, []);

  const [selectedFilters, setSelectedFilters] = useState({
    BA: [],
    BS: [],
    CS: [],
    IS: [],
  });

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

  const filteredCourses = courses.filter((course) =>
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
        courses={filteredCourses}  // Now displaying real courses
        allRequirements={requirements}
        selectedFilters={selectedFilters}
        handleFilterChange={handleFilterChange}
        clearFilters={clearFilters}
        setVisibleCourses={setCourses}
      />
    </div>
  );
};

export default CourseTableMock;
