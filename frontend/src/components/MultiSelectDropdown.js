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

  // Filter out any undefined/null options first.
  const safeOptions = (allRequirements || []).filter(opt => opt != null);

  // Build an array of raw strings (if options are objects, we extract their requirement property)
  const allOptionStrings = safeOptions.map(opt => (typeof opt === "object" ? opt.requirement : opt));
  const isAllSelected = allOptionStrings.length > 0 && selectedForMajor.length === allOptionStrings.length;

  // Handle "Select All"
  const handleSelectAll = () => {
    handleFilterChange(major, isAllSelected ? [] : allOptionStrings);
  };

  return (
    <div className="dropdown cell-container" ref={dropdownRef}>
      <button className="dropdown-btn" onClick={toggleDropdown}>
        Select▼
      </button>

      {isOpen && (
        <div className="dropdown-content">
          {/* "Select All" Option */}
          <label className="dropdown-item">
            <input type="checkbox" checked={isAllSelected} onChange={handleSelectAll} />
            <strong>SELECT ALL</strong>
          </label>

          {/* Individual Options */}
          {safeOptions.length === 0 ? (
            <p className="dropdown-item">No options available</p>
          ) : (
            safeOptions.map((option, index) => {
                // If option is an object, extract its requirement field; else use the option itself.
                const rawOption = typeof option === "object" ? option.requirement : option;
                // Guard against undefined and then apply transformation.
                const formattedOption = (rawOption || "").replace(/^[^-]+---/, "").replace(/---/g, " → ");

                return (
                  <label key={index} className="dropdown-item">
                    <input
                      type="checkbox"
                      checked={selectedForMajor.includes(rawOption)}
                      onChange={(e) => {
                        const newSelection = e.target.checked
                          ? [...selectedForMajor, rawOption]
                          : selectedForMajor.filter((item) => item !== rawOption);
                        handleFilterChange(major, newSelection);
                      }}
                    />
                    {formattedOption}
                  </label>
                );
              })
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
