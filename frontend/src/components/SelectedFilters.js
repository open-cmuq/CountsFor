import React, { useMemo } from "react";

// --- Copied Helper Functions from MultiSelectDropdown ---
// (Ideally, move these to a shared utils file)

// Remove unused displayMap

// Function to format the requirement string (slightly adapted for SelectedFilters context)
const formatRequirementForDisplay = (req, type = null) => {
  let rawReq = typeof req === 'object' ? req.requirement : req;
  if (!rawReq) return '';

  const isGenEd = type === true || (typeof req === 'object' && req.type === true);

  if (isGenEd) {
    if (rawReq.includes("General Education")) {
      rawReq = rawReq.replace(/^.*General Education\s*---/, "");
    } else if (rawReq.includes("University Core Requirements")) {
      const parts = rawReq.split("University Core Requirements");
      if (parts.length > 1) {
        rawReq = parts[1].replace(/^---/, "");
      }
    } else {
      rawReq = rawReq.replace(/^[^-]+---/, "");
    }
  } else {
    rawReq = rawReq.replace(/^[^-]+---/, "");
  }
  return rawReq.replace(/---/g, " → ");
};


const buildNestedGroups = (options) => {
  const tree = {
    "Core Requirements": {},
    "GenEd Requirements": {}
  };

  (options || []).forEach((opt) => {
    if (!opt) return;
    const raw = opt.value || opt.requirement || opt;
    if (!raw) return;
    const isGenEd = typeof opt === 'object' && opt.type === true;
    const formattedText = formatRequirementForDisplay(opt);
    if (!formattedText) return;
    const parts = formattedText.split(" → ");
    const topLevelCategory = isGenEd ? "GenEd Requirements" : "Core Requirements";

    if (parts.length <= 1) {
      if (!tree[topLevelCategory]._items) tree[topLevelCategory]._items = [];
      tree[topLevelCategory]._items.push({ label: parts[0], rawValue: raw });
      return;
    }

    let node = tree[topLevelCategory];
    for (let i = 0; i < parts.length - 1; i++) {
      const key = parts[i];
      if (!node[key]) node[key] = {};
      node = node[key];
    }

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

const getAllRawValues = (node) => {
  let values = [];
  if (node._items) {
    values = values.concat(node._items.map(item => item.rawValue));
  }
  Object.keys(node)
    .filter(key => key !== '_items')
    .forEach(key => {
      values = values.concat(getAllRawValues(node[key]));
    });
  return values;
};
// --- End Helper Functions ---


const SelectedFilters = ({
  selectedFilters,
  handleFilterChange, // Note: This needs adjustment for removing groups
  selectedOfferedSemesters,
  removeOfferedSemester,
  noPrereqs,
  removePrereqFilter,
  allRequirements = {} // Accept allRequirements prop
}) => {
  const majorColors = {
    BA: "#4A68FB",
    BS: "#22AA0A",
    CS: "#CF1314",
    IS: "#FEB204",
  };

  // Use useMemo to build requirement trees only when requirements change
  const requirementTrees = useMemo(() => {
    const trees = {};
    Object.keys(allRequirements).forEach(major => {
      trees[major] = buildNestedGroups(allRequirements[major]);
    });
    return trees;
  }, [allRequirements]);

  // Function to recursively find fully selected groups and generate tags
  const generateTagsForMajor = (major, filters) => {
    const majorTree = requirementTrees[major];
    if (!majorTree || filters.length === 0) return []; // No tree or filters for this major

    let remainingFilters = [...filters]; // Copy to mutate
    const tags = [];

    const findAndTagGroups = (node, groupNamePath = []) => {
      // Check current node (if it's a group, not just a top-level container like "Core")
      if (groupNamePath.length > 0) {
        const groupRawValues = getAllRawValues(node);
        if (groupRawValues.length > 0) {
          const isGroupFullySelected = groupRawValues.every(val => remainingFilters.includes(val));

          if (isGroupFullySelected) {
             // Get the immediate group name (last part of the path)
            const currentGroupName = groupNamePath[groupNamePath.length - 1];
            tags.push(
              <div
                key={`${major}-group-${currentGroupName}`}
                className="filter-tag"
                style={{ backgroundColor: majorColors[major] || "gray" }}
              >
                {/* Button to remove all filters in this group */}
                <button onClick={() => {
                  const currentMajorFilters = selectedFilters[major] || [];
                  const newSelection = currentMajorFilters.filter(f => !groupRawValues.includes(f));
                  handleFilterChange(major, newSelection); // handleFilterChange needs to accept array
                }}><b>×</b></button>
                {`All ${currentGroupName} Requirements`}
              </div>
            );
            // Remove these filters from remainingFilters
            remainingFilters = remainingFilters.filter(f => !groupRawValues.includes(f));
            return; // Don't process children if group is fully selected
          }
        }
      }

      // Recursively check subgroups if not fully selected
      Object.entries(node)
        .filter(([key]) => key !== "_items")
        .forEach(([groupKey, childNode]) => {
          findAndTagGroups(childNode, [...groupNamePath, groupKey]);
        });
    };

    // Start traversal from the major's tree root
    findAndTagGroups(majorTree);

    // Render remaining individual filters
    remainingFilters.forEach(filter => {
      // Attempt to find the original object for better display formatting if needed
      const reqObj = allRequirements[major]?.find(r => r.requirement === filter) || filter;
      const displayedFilter = formatRequirementForDisplay(reqObj).split(' → ').slice(-2).join(' → '); // Keep existing formatting


      tags.push(
        <div
          key={`${major}-${filter}`}
          className="filter-tag"
          style={{ backgroundColor: majorColors[major] || "gray" }}
        >
          {/* Button to remove individual filter */}
          <button onClick={() => {
             const currentMajorFilters = selectedFilters[major] || [];
             const newSelection = currentMajorFilters.filter(f => f !== filter);
             handleFilterChange(major, newSelection); // handleFilterChange needs to accept array
           }}><b>×</b></button>
           {displayedFilter || filter} {/* Fallback to raw filter */}
        </div>
      );
    });

    return tags;
  };


  // Check if there are any filters
  const hasAnyFilters =
    (selectedOfferedSemesters && selectedOfferedSemesters.length > 0) ||
    Object.values(selectedFilters).some((filters) => filters.length > 0) ||
    (noPrereqs !== null);

  if (!hasAnyFilters) return null;

  return (
    <div className="selected-filters">
      {/* Render offered semesters */}
      {selectedOfferedSemesters && selectedOfferedSemesters.map((semester) => (
         <div key={`offered-${semester}`} className="filter-tag" style={{ backgroundColor: "#555" }}>
             <button onClick={() => removeOfferedSemester(semester)}><b>×</b></button>
             {semester}
         </div>
      ))}

      {/* Render Prerequisite filter */}
      {noPrereqs !== null && (
        <div key="prereq-filter" className="filter-tag" style={{ backgroundColor: "#555" }}>
          <button onClick={removePrereqFilter}><b>×</b></button>
          {noPrereqs === true ? 'Has Prerequisites' : 'No Prerequisites'}
        </div>
      )}

      {/* Render requirement filters (using the new logic) */}
      {Object.entries(selectedFilters).flatMap(([major, filters]) =>
         generateTagsForMajor(major, filters)
      )}
    </div>
  );
};

export default SelectedFilters;
