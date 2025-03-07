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

  // Ensure allOptions updates when allRequirements change
  const allOptions = allRequirements?.[major] ?? [];

  // Track selected requirements for this major
  const selectedForMajor = selectedFilters[major] || [];
  const isAllSelected = allOptions.length > 0 && selectedForMajor.length === allOptions.length;

  // Handle "Select All"
  const handleSelectAll = () => {
    handleFilterChange(major, isAllSelected ? [] : allOptions);
  };

  return (
    <div className="dropdown cell-container" ref={dropdownRef}>
      <button className="dropdown-btn" onClick={toggleDropdown}>
        Select ▼
      </button>

      {isOpen && (
        <div className="dropdown-content">
          {/* Debugging: Log available options */}
          {console.log(`Dropdown for ${major}:`, allOptions)}

          {/* "Select All" Option */}
          <label className="dropdown-item">
            <input type="checkbox" checked={isAllSelected} onChange={handleSelectAll} />
            <strong>SELECT ALL</strong>
          </label>

          {/* Individual Options */}
          {allOptions.length === 0 ? (
            <p className="dropdown-item">No requirements available</p>
          ) : (
            allOptions.map((req, index) => (
              <label key={index} className="dropdown-item">
                <input
                  type="checkbox"
                  checked={selectedForMajor.includes(req)}
                  onChange={(e) => {
                    const newSelection = e.target.checked
                      ? [...selectedForMajor, req] // Add selection
                      : selectedForMajor.filter((item) => item !== req); // Remove selection

                    handleFilterChange(major, newSelection);
                  }}
                />
                {req}
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
