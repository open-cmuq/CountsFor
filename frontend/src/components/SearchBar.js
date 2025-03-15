import React, { useEffect, useState } from "react";

const API_BASE_URL = "http://127.0.0.1:8000"; // Ensure correct API base

const SearchBar = ({
  selectedDepartment,
  setSelectedDepartment,
  searchQuery,
  setSearchQuery
}) => {
  const [departments, setDepartments] = useState([]);

  // Fetch departments from API
  useEffect(() => {
    const fetchDepartments = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/departments`);
        if (!response.ok) throw new Error("Failed to fetch departments");

        const data = await response.json();
        console.log("Fetched departments:", data); // Debugging
        setDepartments(data.departments || []); // Ensure valid array
      } catch (error) {
        console.error("Error fetching departments:", error);
      }
    };

    fetchDepartments();
  }, []);

  const handleClearSearch = () => {
    setSearchQuery("");
    setSelectedDepartment("");
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
            console.log("Selected department:", e.target.value); // Debugging
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
              {getDepartmentName(selectedDepartment)} {/* Shows dep_code - name */}
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
