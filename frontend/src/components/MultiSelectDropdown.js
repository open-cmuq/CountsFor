import React, { useState, useRef, useEffect } from "react";

const MultiSelectDropdown = ({ major, allRequirements, selectedFilters, handleFilterChange, clearFilters }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // For general visibility of dropdown box
  const toggleDropdown = () => setIsOpen(!isOpen);

  // To close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Get currently selected filters for the major
  const selectedForMajor = selectedFilters[major] || [];

  // Check if all options or select all button is selected
  const allOptions = allRequirements[major] || [];
  const isAllSelected = allOptions.length > 0 && selectedForMajor.length === allOptions.length;

  // Handle "Select All" functionality
  const handleSelectAll = () => {
    if (isAllSelected) {
      handleFilterChange(major, []); // Deselect
    } else {
      handleFilterChange(major, allOptions); // Select
    }
  };

  return (
    <div className="dropdown cell-container" ref={dropdownRef}>
      <button className="dropdown-btn" onClick={toggleDropdown}>
        Select ▼
      </button>

      {isOpen && (
        <div className="dropdown-content">


          {/* Individual Options */}
          {allOptions.map((req) => (
            <label key={req} className="dropdown-item">
              <input
                type="checkbox"
                checked={selectedForMajor.includes(req)}
                onChange={(e) => {
                  const newSelection = e.target.checked
                    ? [...selectedForMajor, req] // Add if checked
                    : selectedForMajor.filter((item) => item !== req); // Remove if unchecked

                  handleFilterChange(major, newSelection);
                }}
              />
              {req}
            </label>
          ))}

            {/* "Select All" Option */}
            <label className="dropdown-item">
            <input
              type="checkbox"
              checked={isAllSelected}
              onChange={handleSelectAll}
            />
            <strong>SELECT ALL</strong>
          </label>

          {/* Clear Selection Button */}
          <label className="clear-btn">
          <button
            className="clear-btn"
            onClick={() => {
              clearFilters(major);
              setIsOpen(false); 
            }}
          >
            Clear Selection
          </button>
          </label>
        </div>
      )}
    </div>
  );
};

export default MultiSelectDropdown;
