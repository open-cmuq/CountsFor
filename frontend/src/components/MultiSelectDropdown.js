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
  
  const buildNestedGroups = (options) => {
    const tree = {};
  
    options.forEach((opt) => {
      const raw = typeof opt === "object" ? opt.requirement : opt;
      const parts = raw.split("---").slice(1); // Remove major
  
      let node = tree;
      for (let i = 0; i < parts.length - 1; i++) {
        const key = parts[i];
        if (!node[key]) node[key] = {};
        node = node[key];
      }
  
      const label = parts[parts.length - 1];
      if (!node._items) node._items = [];
      node._items.push({ label, rawValue: raw });
    });
  
    return tree;
  };

  const renderGroupTree = (node, path = "") => {
    return Object.entries(node)
    .filter(([key]) => key !== "_items")
    .map(([group, child]) => {
      const isExpanded = expandedGroups[path + group];
      const toggle = () =>
        setExpandedGroups((prev) => ({
          ...prev,
          [path + group]: !isExpanded,
        }));
  
      return (
        <div key={path + group} className="dropdown-group">
          <div className="dropdown-group-label" onClick={toggle}>
            <span>{group}</span>
            <span>{isExpanded ? "▼" : "▶"}</span>
          </div>
  
          {isExpanded && (
  <div className="dropdown-subgroup">

    {/* Select all in group */}
    {child._items?.length > 1 && (
      <label className="dropdown-item nested">
        <input
          type="checkbox"
          checked={child._items.every(item => selectedForMajor.includes(item.rawValue))}
          onChange={(e) => {
            const groupValues = child._items.map(item => item.rawValue);
            const newSelection = e.target.checked
              ? [...new Set([...selectedForMajor, ...groupValues])]
              : selectedForMajor.filter(val => !groupValues.includes(val));
            handleFilterChange(major, newSelection);
          }}
        />
        <strong>Select All in {group}</strong>
      </label>
    )}

    {child._items?.map(({ rawValue, label }) => (
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

    {renderGroupTree(child, path + group + " > ")}
  </div>
)}

        </div>
      );
    });
  };
  
  
  // Build an array of raw strings (if options are objects, we extract their requirement property)
  const allOptionStrings = safeOptions.map(opt => (typeof opt === "object" ? opt.requirement : opt));
  const isAllSelected = allOptionStrings.length > 0 && selectedForMajor.length === allOptionStrings.length;

  // Handle "Select All"
  const handleSelectAll = () => {
    handleFilterChange(major, isAllSelected ? [] : allOptionStrings);
  };

  const [expandedGroups, setExpandedGroups] = useState({});


  return (
    <div
    className={`dropdown cell-container ${major === "offered" ? "dropdown-offered" : ""}`}
    ref={dropdownRef}
    >


      <button className="dropdown-btn" onClick={toggleDropdown}>
        Select▼
      </button>

      {isOpen && (
                <div className="dropdown-content">
            <label className="select-all-label">
            <button
        className="select-all-btn"
        onClick={() => handleSelectAll()}
        >
        {isAllSelected ? "DeSelect All" : "Select All"}
        </button>
        </label>

          {/* Clear Selection Button */}
          <label className="select-all-label">
            <button
              className="select-all-btn"
              onClick={() => {
                clearFilters(major);
                setIsOpen(false);
              }}
            >
              Clear All
            </button>
          </label>

          {/* Individual Options */}
          {safeOptions.length === 0 ? (
            <p className="dropdown-item">No options available</p>
            ) : safeOptions.every(opt => !(typeof opt === 'string' ? opt.includes('---') : (opt.requirement || '').includes('---'))) ? (
            safeOptions.map((opt, index) => {
                const raw = typeof opt === "object" ? opt.requirement : opt;
                return (
                <label key={index} className="dropdown-item">
                    <input
                    type="checkbox"
                    checked={selectedForMajor.includes(raw)}
                    onChange={(e) => {
                        const newSelection = e.target.checked
                        ? [...selectedForMajor, raw]
                        : selectedForMajor.filter(item => item !== raw);
                        handleFilterChange(major, newSelection);
                    }}
                    />
                    {raw}
                </label>
                );
            })
            ) : (
            renderGroupTree(buildNestedGroups(safeOptions))
            )}
        </div>
      )}
    </div>
  );
};

export default MultiSelectDropdown;
