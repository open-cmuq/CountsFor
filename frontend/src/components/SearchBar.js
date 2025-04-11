import React, { useEffect, useState } from "react";
import MultiSelectDropdown from "./MultiSelectDropdown";
import { formatCourseCode } from './utils/courseCodeFormatter';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const SearchBar = ({
  selectedDepartments,
  setSelectedDepartments,
  searchQuery,
  setSearchQuery,
  noPrereqs,
  setNoPrereqs,
  offeredQatar,
  setOfferedQatar,
  offeredPitts,
  setOfferedPitts,
  coreOnly,       // new prop for Core checkbox
  setCoreOnly,    // setter for Core checkbox
  genedOnly,      // new prop for GenEd checkbox
  setGenedOnly    // setter for GenEd checkbox
}) => {
  const [departments, setDepartments] = useState([]);

  // Set default values on component mount if not already set
  useEffect(() => {
    // Default location to Qatar if not already set
    if (offeredQatar === null) {
      setOfferedQatar(true);
    }

    // Default course type to both Core and GenEd if not already set
    if (coreOnly === null && genedOnly === null) {
      setCoreOnly(true);
      setGenedOnly(true);
    }
  }, [offeredQatar, coreOnly, genedOnly, setOfferedQatar, setCoreOnly, setGenedOnly]);

  // Fetch departments from API
  useEffect(() => {
    const fetchDepartments = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/departments`);
        if (!response.ok) throw new Error("Failed to fetch departments");
        const data = await response.json();
        console.log("Fetched departments:", data);
        setDepartments(data.departments || []);
      } catch (error) {
        console.error("Error fetching departments:", error);
      }
    };

    fetchDepartments();
  }, []);

  // Function to get department name based on selected dep_code
  const getDepartmentName = (depCode) => {
    const dept = departments.find((dept) => dept.dep_code === depCode);
    return dept ? `${dept.dep_code} - ${dept.name}` : depCode;
  };

  // Modify the search input handler
  const handleSearchChange = (e) => {
    const formattedCode = formatCourseCode(e.target.value);
    setSearchQuery(formattedCode);
  };

  return (
    <div className="search-container">
      <label className="search-label">SEARCH</label>
      <div className="search-bar-row">
        {/* Course Search Input */}
        <input
          type="text"
          placeholder="Search for a specific course number"
          value={searchQuery}
          onChange={handleSearchChange}
          className="text-input"
        />

      {/* Department Dropdown */}
      <div className="filter-group">
        <label className="filter-label">Departments</label>
        <MultiSelectDropdown
          major="department"
          showSelectedInButton={false}
          wrapperClassName="department-dropdown-wrapper"
          allRequirements={departments.map((d) => ({
            value: d.dep_code,
            label: `${d.dep_code} - ${d.name}`,
          }))}
          selectedFilters={{ department: selectedDepartments }}
          handleFilterChange={(major, selected) => setSelectedDepartments(selected)}
          clearFilters={() => setSelectedDepartments([])}
        />
      </div>

      <div className="filter-group">
        <label className="filter-label">Location</label>
        <MultiSelectDropdown
          major="location"
          wrapperClassName="location-dropdown-wrapper"
          showSelectedInButton={true}
          hideSelectButtons={true}
          allRequirements={["qatar", "pitts"]}
          selectedFilters={{ location: [
            ...(offeredQatar ? ["qatar"] : []),
            ...(offeredPitts ? ["pitts"] : [])
          ] }}
          handleFilterChange={(major, selected) => {
            setOfferedQatar(selected.includes("qatar") ? true : null);
            setOfferedPitts(selected.includes("pitts") ? true : null);
          }}
          clearFilters={() => {
            setOfferedQatar(null);
            setOfferedPitts(null);
          }}
        />
      </div>

      <div className="filter-group">
        <label className="filter-label">Course Type</label>
        <MultiSelectDropdown
          major="courseType"
          wrapperClassName="course-type-dropdown-wrapper"
          showSelectedInButton={true}
          hideSelectButtons={true}
          allRequirements={["core", "gened"]}
          selectedFilters={{ courseType: [
            ...(coreOnly ? ["core"] : []),
            ...(genedOnly ? ["gened"] : [])
          ] }}
          handleFilterChange={(major, selected) => {
            setCoreOnly(selected.includes("core") ? true : null);
            setGenedOnly(selected.includes("gened") ? true : null);
          }}
          clearFilters={() => {
            setCoreOnly(null);
            setGenedOnly(null);
          }}
        />
    </div>


      {/* Search & Clear Buttons */}
      <button className="search-btn">🔍</button>
    </div>

      {/*Display Selected Filters*/}
      {(selectedDepartments.length > 0 || searchQuery) && (
  <div className="selected-filters">
    {selectedDepartments.map((depCode) => (
      <span key={depCode} className="filter-tag">
        <button
          onClick={() =>
            setSelectedDepartments((prev) =>
              prev.filter((code) => code !== depCode)
            )
          }
        >
          <span style={{ fontWeight: "bold", marginRight: "4px" }}>×</span>
        </button>
        {getDepartmentName(depCode)}
      </span>
    ))}

    {searchQuery && (
      <span className="filter-tag">
        <button onClick={() => setSearchQuery("")}>
          <span style={{ fontWeight: "bold", marginRight: "4px" }}>×</span>
        </button>
        {searchQuery}
      </span>
    )}
  </div>
)}


    </div>
  );
};

export default SearchBar;
