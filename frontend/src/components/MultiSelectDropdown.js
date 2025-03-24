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
  
  const groupedOptions = {};
  safeOptions.forEach((opt) => {
    const raw = typeof opt === "object" ? opt.requirement : opt;
    const parts = raw.split("---").slice(1); // skip major name

    if (!parts.length) return;

    const parent = parts[0]; // top-level group
    const label = parts.slice(1).join(" → ") || parent;

    if (!groupedOptions[parent]) groupedOptions[parent] = [];

    groupedOptions[parent].push({
        rawValue: raw,
        label,
    });
    });

  // Build an array of raw strings (if options are objects, we extract their requirement property)
  const allOptionStrings = safeOptions.map(opt => (typeof opt === "object" ? opt.requirement : opt));
  const isAllSelected = allOptionStrings.length > 0 && selectedForMajor.length === allOptionStrings.length;

  // Handle "Select All"
  const handleSelectAll = () => {
    handleFilterChange(major, isAllSelected ? [] : allOptionStrings);
  };

  const [expandedGroups, setExpandedGroups] = useState({});

  const toggleGroup = (group) => {
    setExpandedGroups((prev) => ({
      ...prev,
      [group]: !prev[group],
    }));
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
            Object.entries(groupedOptions).map(([group, items]) => (
                <div key={group} className="dropdown-group">
                <div
                    className="dropdown-group-label"
                    onClick={() => toggleGroup(group)}
                    style={{ cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "space-between" }}
                >
                    <strong>{group}</strong>
                    <span>{expandedGroups[group] ? "▼" : "▶"}</span>
                </div>

                {expandedGroups[group] && (
                    <div className="dropdown-subgroup">
                    {items.map(({ rawValue, label }) => (
                        <label key={rawValue} className="dropdown-item nested">
                        <input
                            type="checkbox"
                            checked={selectedForMajor.includes(rawValue)}
                            onChange={(e) => {
                            const newSelection = e.target.checked
                                ? [...selectedForMajor, rawValue]
                                : selectedForMajor.filter((item) => item !== rawValue);
                            handleFilterChange(major, newSelection);
                            }}
                        />
                        {label}
                        </label>
                    ))}
                    </div>
                )}
                </div>
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
