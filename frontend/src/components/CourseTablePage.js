import React, { useState, useEffect } from "react";
import "../styles.css";
import SearchBar from "./SearchBar";
import CourseTable from "./CourseTable";
import SelectedFilters from "./SelectedFilters";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const CourseTablePage = () => {
  const [departments, setDepartments] = useState([]);  // Ensure it's an array
  const [selectedDepartment, setSelectedDepartment] = useState("");
  const [requirements, setRequirements] = useState({ BA: [], BS: [], CS: [], IS: [] });
  const [allCourses, setAllCourses] = useState([]);
  const [filteredCourses, setFilteredCourses] = useState([]);
  const [selectedFilters, setSelectedFilters] = useState({ BA: [], BS: [], CS: [], IS: [] });
  const [searchQuery, setSearchQuery] = useState("");

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

        console.log("✅ Requirements Fetched from API:", data);

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

        console.log("✅ Transformed Requirements for UI:", transformedRequirements);
        setRequirements(transformedRequirements);
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
        setAllCourses(data.courses);
        setFilteredCourses(data.courses);
      } catch (error) {
        console.error("Error fetching courses:", error);
      }
    };

    fetchCourses();
  }, []);

  useEffect(() => {
    setFilteredCourses(
      allCourses
        .filter((course) =>
          (selectedDepartment === "" || course.department === selectedDepartment) &&
          (searchQuery === "" || course.course_code.includes(searchQuery)) &&
          Object.keys(selectedFilters).every((major) => {
            if (selectedFilters[major].length === 0) return true;
            const courseReqs = course.requirements?.[major] || [];
            return selectedFilters[major].some((req) =>
              courseReqs.map((r) => r.toLowerCase()).includes(String(req).toLowerCase())
            );
          })
        )
    );
  }, [searchQuery, selectedDepartment, selectedFilters, allCourses]);


  const handleFilterChange = (major, newSelection) => {
    setSelectedFilters((prev) => ({
      ...prev,
      [major]: Array.isArray(newSelection) ? newSelection : prev[major].filter((filter) => filter !== newSelection),
    }));
  };

  const clearFilters = (major) => {
    setSelectedFilters((prev) => ({ ...prev, [major]: [] }));
  };

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
        allCourses={allCourses}
        allRequirements={requirements}
        selectedFilters={selectedFilters}
        handleFilterChange={handleFilterChange}
        clearFilters={clearFilters}
        setVisibleCourses={setFilteredCourses}
      />
    </div>
  );
};

export default CourseTablePage;
