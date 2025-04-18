import React, { useState, useRef, useEffect } from "react";

const MultiSelectDropdown = ({
  major,
  allRequirements,
  selectedFilters,
  handleFilterChange,
  clearFilters,
  showSelectedInButton = false,
  hideSelectButtons = false,
  wrapperClassName = ""
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [tempSelection, setTempSelection] = useState([]);
  const dropdownRef = useRef(null);
  const displayMap = {
    qatar: "Qatar",
    pitts: "Pittsburgh",
    core: "Core",
    gened: "Gen-Ed",
    all: "All Courses",
    with: "Has Pre-reqs",
    without: "No Pre-reqs",
  };

  // Toggle dropdown visibility
  const toggleDropdown = () => setIsOpen(!isOpen);

  useEffect(() => {
    if (isOpen) {
      const current = major ? (selectedFilters[major] || []) : selectedFilters;
      setTempSelection(current);
    }
  }, [isOpen, major, selectedFilters]);  

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

  // Function to format the requirement string the same way as in the table
  const formatRequirementForDisplay = (req) => {
    // Early return for non-requirement formats (e.g., departments, location)
    if (major === 'department' || major === 'location' || major === 'courseType' || major === 'offered' || major === 'prereq') {
      return typeof req === 'object' ? (req.label || '') : req || '';
    }

    // Handle requirement formatting
    let rawReq = typeof req === 'object' ? req.requirement : req;

    // Guard against undefined or null values
    if (!rawReq) return '';

    const isGenEd = typeof req === 'object' && req.type === true;

    // For GenEd requirements, handle different formats
    if (isGenEd) {
      if (rawReq.includes("General Education")) {
        // Traditional format with "General Education"
        rawReq = rawReq.replace(/^.*General Education\s*---/, "");
      } else if (rawReq.includes("University Core Requirements")) {
        // BA format using "University Core Requirements"
        // Extract everything after the first occurrence of "University Core Requirements"
        const parts = rawReq.split("University Core Requirements");
        if (parts.length > 1) {
          // Remove the leading "---" if present
          rawReq = parts[1].replace(/^---/, "");
        }
      } else {
        // For any other GenEd format, just remove the initial prefix
        rawReq = rawReq.replace(/^[^-]+---/, "");
      }
    } else {
      // For Core requirements, just remove the initial prefix
      rawReq = rawReq.replace(/^[^-]+---/, "");
    }

    // Replace all --- with arrows
    return rawReq.replace(/---/g, " → ");
  };

  const buildNestedGroups = (options) => {
    // For non-major requirement dropdowns, return empty tree
    // These are handled separately in the render function
    if (major === 'department' || major === 'location' || major === 'courseType' ||
        major === 'offered' || major === 'prereq') {
      return {};
    }

    // First, separate options into Core and GenEd categories
    const tree = {
      "Core Requirements": {},
      "GenEd Requirements": {}
    };

    options.forEach((opt) => {
      // Skip invalid options
      if (!opt) return;

      const raw = opt.value || opt.requirement || opt;

      // Skip if raw is undefined/null
      if (!raw) return;

      const isGenEd = typeof opt === 'object' && opt.type === true;

      // Get the formatted text that matches what's shown in the table
      const formattedText = formatRequirementForDisplay(opt);

      // Skip if no formatted text
      if (!formattedText) return;

      // Split by arrows to get the hierarchical parts
      const parts = formattedText.split(" → ");

      // Determine the top-level category based on the requirement type
      const topLevelCategory = isGenEd ? "GenEd Requirements" : "Core Requirements";

      // If there's only one part (no hierarchy), put directly under Core/GenEd
      if (parts.length <= 1) {
        if (!tree[topLevelCategory]._items) tree[topLevelCategory]._items = [];
        tree[topLevelCategory]._items.push({ label: parts[0], rawValue: raw });
        return;
      }

      // For hierarchical requirements, build nested structure under Core or GenEd
      let node = tree[topLevelCategory];
      for (let i = 0; i < parts.length - 1; i++) {
        const key = parts[i];
        if (!node[key]) node[key] = {};
        node = node[key];
      }

      // The last part is the leaf item
      const label = parts[parts.length - 1];
      if (!node._items) node._items = [];
      node._items.push({ label, rawValue: raw });
    });

    // Remove empty categories
    if (Object.keys(tree["Core Requirements"]).length === 0 &&
        (!tree["Core Requirements"]._items || tree["Core Requirements"]._items.length === 0)) {
      delete tree["Core Requirements"];
    }

    if (Object.keys(tree["GenEd Requirements"]).length === 0 &&
        (!tree["GenEd Requirements"]._items || tree["GenEd Requirements"]._items.length === 0)) {
      delete tree["GenEd Requirements"];
    }

    return tree;
  };

  const renderGroupTree = (node, path = "") => {
    return (
      <>
        {/* Render top-level items first */}
        {node._items?.map(({ rawValue, label }) => (
        <div key={rawValue} className="dropdown-group">
          <label className="dropdown-group-label dropdown-item checkbox-right">
            <span className="item-text">{displayMap[rawValue] || label}</span>
            <input
              type="checkbox"
              checked={tempSelection.includes(rawValue)}
              onChange={(e) => {
                const newSelection = e.target.checked
                  ? [...tempSelection, rawValue]
                  : tempSelection.filter((item) => item !== rawValue);
                setTempSelection(newSelection);
              }}
            />
          </label>
        </div>
      ))}

        {/* Then render nested groups */}
        {Object.entries(node)
          .filter(([key]) => key !== "_items")
          .map(([group, child]) => {
            const isExpanded = expandedGroups[path + group];
            const toggle = () =>
              setExpandedGroups((prev) => ({
                ...prev,
                [path + group]: !isExpanded,
              }));

            // Skip rendering if the group has no items or subgroups
            const hasItems = child._items && child._items.length > 0;
            const hasSubgroups = Object.keys(child).filter(k => k !== "_items").length > 0;
            if (!hasItems && !hasSubgroups) return null;

            return (
              <div key={path + group} className="dropdown-group">
                <div className="dropdown-group-label" onClick={toggle}>
                <span>
                  {group === "Core Requirements" ? (
                    <>
                      <strong>Core</strong> Requirements
                    </>
                  ) : group === "GenEd Requirements" ? (
                    <>
                      <em>Gen-Ed</em> Requirements
                    </>
                  ) : (
                    group
                  )}
                </span>
                <span>{isExpanded ? "▼" : "▶"}</span>
                </div>

                {isExpanded && (
                  <div className="dropdown-subgroup">
                    {/* Select all in group */}
                    {child._items?.length > 1 && (
                      <label className="dropdown-item nested">
                      <input
                        type="checkbox"
                        checked={child._items.every(item =>
                          tempSelection.includes(item.rawValue)
                        )}
                        onChange={(e) => {
                          const groupValues = child._items.map(item => item.rawValue);
                          const newSelection = e.target.checked
                            ? [...new Set([...tempSelection, ...groupValues])]
                            : tempSelection.filter(val => !groupValues.includes(val));
                          setTempSelection(newSelection); 
                        }}
                      />
                      <strong>Select All in {group}</strong>
                      </label>
                    )}

                    {/* Recursively render children */}
                    {renderGroupTree(child, path + group + " > ")}
                  </div>
                )}
              </div>
            );
          })}
      </>
    );
  };

  // Build an array of raw strings (if options are objects, we extract their requirement property)
  const allOptionStrings = safeOptions.map(opt => (typeof opt === "object" ? opt.requirement : opt));
  const isAllSelected = allOptionStrings.length > 0 && selectedForMajor.length === allOptionStrings.length;

  // Handle "Select All"
  const handleSelectAll = () => {
    handleFilterChange(major, isAllSelected ? [] : allOptionStrings);
  };

  // State to track expanded groups
  const [expandedGroups, setExpandedGroups] = useState({});

  // Check if the current selection is different from the temp selection
  const isDirty = () => {
    const current = selectedForMajor.slice().sort();
    const temp = tempSelection.slice().sort();
    return current.length !== temp.length || !current.every((v, i) => v === temp[i]);
  };
  


  return (
  <div
    className={`dropdown cell-container ${major === "offered" ? "dropdown-offered" : ""} ${wrapperClassName || ""}`}
    ref={dropdownRef}
  >


    <button className="dropdown-btn" onClick={toggleDropdown}>
      {showSelectedInButton && selectedForMajor.length > 0
        ? selectedForMajor
            .map((val) => {
              if (val === "core") return <strong key={val}>Core</strong>;
              if (val === "gened") return <em key={val}>Gen-Ed</em>;
              return displayMap[val] || val;
            })
            .reduce((prev, curr, i) => [prev, ", ", curr])
        : ["BA", "BS", "CS", "IS"].includes(major)
          ? "Select Requirements ▼"
          : "Select ▼"}
    </button>

      {isOpen && (
        <div className="dropdown-content">

        {!hideSelectButtons && (
          <div className="select-buttons-row">
            <button
              className="select-all-btn"
              onClick={() => handleSelectAll()}
            >
              {isAllSelected ? "Deselect All" : "Select All"}
            </button>

            <button
              className="select-all-btn clear-btn"
              onClick={() => {
                if (!selectedForMajor.length) return; // safeguard
                clearFilters(major);
                setIsOpen(false);
              }}
              disabled={selectedForMajor.length === 0}
            >
              Clear All
            </button>
          </div>
        )}

        {/* Always show Apply/Cancel */}
        <button
          className={`drop-apply-btn ${isDirty() ? 'active' : 'disabled'}`}
          onClick={() => {
            if (!isDirty()) return; 
            handleFilterChange(major, tempSelection);
            setIsOpen(false);
          }}
          disabled={!isDirty()} 
        >
          Apply Filters
        </button>

          {/* Individual Options */}
          {safeOptions.length === 0 ? (
            <p className="dropdown-item">No options available</p>
          ) : (
            /* For non-requirement dropdowns, render a simple list */
            major === 'department' || major === 'location' || major === 'courseType' ||
            major === 'offered' || major === 'prereq' ? (
              safeOptions.map((opt, index) => {
                const raw = typeof opt === "object" ? (opt.value || opt.requirement || opt.dep_code) : opt;
                let label;

                if (typeof opt === "object") {
                  // Handle different object formats
                  if (major === 'department' && opt.label) {
                    label = opt.label;
                  } else if (major === 'department' && opt.dep_code) {
                    label = `${opt.dep_code} - ${opt.name || ''}`;
                  } else {
                    label = opt.label || raw;
                  }
                } else {
                  label = opt;
                }

                return (
                  <label key={index} className="dropdown-item">
                  <input
                    type="checkbox"
                    checked={tempSelection.includes(raw)}
                    onChange={(e) => {
                      const newSelection = e.target.checked
                        ? [...tempSelection, raw]
                        : tempSelection.filter(item => item !== raw);
                      setTempSelection(newSelection); 
                    }}
                  />
                    {raw === "core" ? (
                      <strong>Core</strong>
                    ) : raw === "gened" ? (
                      <em>Gen-Ed</em>
                    ) : (
                      displayMap[raw] || label
                    )}
                  </label>
                );
              })
            ) : (
              /* For major requirements - use the nested Core/GenEd structure */
              renderGroupTree(buildNestedGroups(safeOptions))
            )
          )}
        </div>
      )}
    </div>
  );
};

export default MultiSelectDropdown;
