import React, { useState, useRef, useEffect } from "react";

const MultiSelectDropdown = ({ major, allRequirements, selectedFilters, handleFilterChange, clearFilters }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Toggle dropdown visibility
  const toggleDropdown = () => setIsOpen(!isOpen);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Use the key from selectedFilters if major is provided; otherwise, assume selectedFilters is directly an array.
  const selectedForMajor = major ? (selectedFilters[major] || []) : selectedFilters;
  const options = allRequirements || [];

  const isAllSelected = options.length > 0 && selectedForMajor.length === options.length;

  // Handle "Select All"
  const handleSelectAll = () => {
    handleFilterChange(major, isAllSelected ? [] : options);
  };

  return (
    <div className="dropdown cell-container" ref={dropdownRef}>
      <button className="dropdown-btn" onClick={toggleDropdown}>
        Select ▼
      </button>

      {isOpen && (
        <div className="dropdown-content">
          {/* "Select All" Option */}
          <label className="dropdown-item">
            <input type="checkbox" checked={isAllSelected} onChange={handleSelectAll} />
            <strong>SELECT ALL</strong>
          </label>

          {/* Individual Options */}
          {options.length === 0 ? (
            <p className="dropdown-item">No options available</p>
          ) : (
            options.map((option, index) => (
              <label key={index} className="dropdown-item">
                <input
                  type="checkbox"
                  checked={selectedForMajor.includes(option)}
                  onChange={(e) => {
                    const newSelection = e.target.checked
                      ? [...selectedForMajor, option]
                      : selectedForMajor.filter((item) => item !== option);
                    handleFilterChange(major, newSelection);
                  }}
                />
                {option}
              </label>
            ))
          )}

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
