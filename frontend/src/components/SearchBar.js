import React, { useEffect, useState } from "react";
import { formatCourseCode } from './utils/courseCodeFormatter';

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

  // Modify the search input handler
  const handleSearchChange = (e) => {
    const formattedCode = formatCourseCode(e.target.value);
    setSearchQuery(formattedCode);
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
          onChange={handleSearchChange}
          className="text-input"
        />

        <div className="checkbox-group">
          <label>
            <input
              type="checkbox"
              checked={noPrereqs === false}
              onChange={(e) =>
                setNoPrereqs(e.target.checked ? false : null)
              }
            />
            No Pre-reqs
          </label>
          <label>
            <input
              type="checkbox"
              checked={offeredQatar === true}
              onChange={(e) =>
                setOfferedQatar(e.target.checked ? true : null)
              }
            />
            Qatar
          </label>
          <label>
            <input
              type="checkbox"
              checked={offeredPitts === true}
              onChange={(e) =>
                setOfferedPitts(e.target.checked ? true : null)
              }
            />
            Pitts
          </label>
          {/* New checkboxes for requirement type filtering */}
          <label>
            <input
              type="checkbox"
              checked={coreOnly === true}
              onChange={(e) =>
                setCoreOnly(e.target.checked ? true : null)
              }
            />
            Core
          </label>
          <label>
            <input
              type="checkbox"
              checked={genedOnly === true}
              onChange={(e) =>
                setGenedOnly(e.target.checked ? true : null)
              }
            />
            GenEd
          </label>
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
