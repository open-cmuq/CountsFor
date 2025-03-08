import React, { useState, useEffect } from "react";
import "../styles.css";
import SearchBar from "./SearchBar";
import CourseTable from "./CourseTable";
import SelectedFilters from "./SelectedFilters";

const API_BASE_URL = "http://127.0.0.1:8000";

const CourseTablePage = () => {
  const [departments, setDepartments] = useState([]);  // Ensure it's an array
  const [requirements, setRequirements] = useState({ BA: [], BS: [], CS: [], IS: [] });
  const [courses, setCourses] = useState([]);
  const [selectedFilters, setSelectedFilters] = useState({ BA: [], BS: [], CS: [], IS: [] });
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDepartment, setSelectedDepartment] = useState("");

  useEffect(() => {
    const fetchDepartments = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/departments`);
        if (!response.ok) throw new Error("Failed to fetch departments");
        const data = await response.json();
        console.log("Fetched Departments from API:", data);
        setDepartments(data.departments || []);  // Ensure we extract the array properly
      } catch (error) {
        console.error("Error fetching departments:", error);
        setDepartments([]);  // Ensure it's always an array
      }
    };

    fetchDepartments();
  }, []);

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
        departments={departments}  // Now using real API data
        selectedDepartment={selectedDepartment}
        setSelectedDepartment={setSelectedDepartment}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
      />
      <SelectedFilters selectedFilters={selectedFilters} handleFilterChange={handleFilterChange} />
      <CourseTable
        courses={filteredCourses}
        allRequirements={requirements}
        selectedFilters={selectedFilters}
        handleFilterChange={handleFilterChange}
        clearFilters={clearFilters}
        setVisibleCourses={setCourses}
      />
    </div>
  );
};

export default CourseTablePage;
