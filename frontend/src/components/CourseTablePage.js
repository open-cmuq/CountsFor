import React, { useState } from "react";
import mockCourses from "../mockData/courses";
import mockRequirements from "../mockData/requirements";
import "../styles.css";
import SearchBar from "./SearchBar";
import CourseTable from "./CourseTable";
import SelectedFilters from "./SelectedFilters";

const CourseTableMock = () => {
  // console.log("Initial Requirements:", mockRequirements);
  // console.log(typeof mockRequirements);

  const categorizeRequirements = (requirements) => {
    // console.log("Mock Requirements Data:", JSON.stringify(mockRequirements, null, 2));
    const categorized = { BA: [], BS: [], CS: [], IS: [] };
  
    // console.log(requirements)
    requirements.forEach(({ requirement, audit_id }) => {
      if (!audit_id) return; // Ignore invalid entries
  
      if (audit_id.endsWith("_0")) {
        // Core requirements
        if (audit_id.startsWith("is")) categorized.IS.push(requirement);
        if (audit_id.startsWith("bs")) categorized.BS.push(requirement);
        if (audit_id.startsWith("cs")) categorized.CS.push(requirement);
        if (audit_id.startsWith("ba")) categorized.BA.push(requirement);
      } else if (audit_id.endsWith("_1")) {
        // General education requirements
        if (audit_id.startsWith("is")) categorized.IS.push(requirement);
        if (audit_id.startsWith("bs")) categorized.BS.push(requirement);
        if (audit_id.startsWith("cs")) categorized.CS.push(requirement);
        if (audit_id.startsWith("ba")) categorized.BA.push(requirement);
      }
    });
    
  
    return categorized;
  };
  // console.log("Categorized Requirements:", categorizedReqs);
  // console.log("CS Requirements:", categorizedReqs["CS"]);
  // console.log("IS Requirements:", categorizedReqs["IS"]);

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

  // const removeCourse = (courseCode) => {
  //   setVisibleCourses((prev) => prev.filter((course) => course.course_code !== courseCode));
  // };

  const filteredCourses = visibleCourses.filter((course) =>
    (selectedDepartment === "" || course.department === selectedDepartment) &&
    (searchQuery === "" || course.course_code.includes(searchQuery)) &&
    Object.keys(selectedFilters).every((major) => {
      if (selectedFilters[major].length === 0) return true;
  
      // Ensure course has requirements for this major
      const courseReqs = course.requirements?.[major] || [];
  
      // Convert both to lowercase for consistent comparison
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
        allRequirements={categorizeRequirements(mockRequirements)}
        selectedFilters={selectedFilters}
        handleFilterChange={handleFilterChange}
        clearFilters={clearFilters}
        setVisibleCourses={setVisibleCourses} 
      />
    </div>
  );
};

export default CourseTableMock;
