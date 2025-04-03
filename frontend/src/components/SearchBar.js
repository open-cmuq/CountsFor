import React, { useEffect, useState } from "react";
import MultiSelectDropdown from "./MultiSelectDropdown";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const SearchBar = ({
  selectedDepartment,
  setSelectedDepartment,
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

  const handleClearSearch = () => {
    setSearchQuery("");
    setSelectedDepartment("");
    setNoPrereqs(null);
    setOfferedQatar(null);
    setOfferedPitts(null);
    setCoreOnly(null);
    setGenedOnly(null);
  };

  // Function to get department name based on selected dep_code
  const getDepartmentName = (depCode) => {
    const dept = departments.find((dept) => dept.dep_code === depCode);
    return dept ? `${dept.dep_code} - ${dept.name}` : depCode;
  };

  return (
    <div className="search-container">
      <label className="search-label">SEARCH</label>
      <div className="search-inputs">
        {/* Department Dropdown */}
        <select
          value={selectedDepartment}
          onChange={(e) => {
            console.log("Selected department:", e.target.value);
            setSelectedDepartment(e.target.value);
          }}
          className="search-dropdown"
        >
          <option value="">Choose a department</option>
          {departments.map((dept, index) => (
            <option key={dept.dep_code || index} value={dept.dep_code}>
              {dept.dep_code} - {dept.name}
            </option>
          ))}
        </select>

        {/* Course Search Input */}
        <input
          type="text"
          placeholder="Specific course number"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="text-input"
        />

  <div className="search-filters">
    <div className="filter-group">
      <label className="filter-label">Location</label>
      <MultiSelectDropdown
        major="location"
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
  </div>


        {/* Search & Clear Buttons */}
        <button className="search-btn">🔍</button>
        <button onClick={handleClearSearch} className="search-clear-btn">
          CLEAR SEARCH
        </button>
      </div>

      {/* Display Selected Filters */}
      {(selectedDepartment || searchQuery) && (
        <div className="selected-filters">
          {selectedDepartment && (
            <span className="filter-tag">
              {getDepartmentName(selectedDepartment)}
              <button onClick={() => setSelectedDepartment("")}>×</button>
            </span>
          )}
          {searchQuery && (
            <span className="filter-tag">
              {searchQuery}
              <button onClick={() => setSearchQuery("")}>×</button>
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchBar;
