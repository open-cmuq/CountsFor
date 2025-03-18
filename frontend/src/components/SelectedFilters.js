import React from "react";

const SelectedFilters = ({
  selectedFilters,
  handleFilterChange,
  selectedOfferedSemesters,
  removeOfferedSemester
}) => {
  const majorColors = {
    BA: "#4A68FB",
    BS: "#22AA0A",
    CS: "#CF1314",
    IS: "#FFC033",
  };

  // Check if there are any filters (offered semesters or requirement filters)
  const hasAnyFilters =
    (selectedOfferedSemesters && selectedOfferedSemesters.length > 0) ||
    Object.keys(selectedFilters).some((major) => selectedFilters[major].length > 0);

  if (!hasAnyFilters) return null;

  return (
    <div className="selected-filters">
      {/* Render offered semesters first */}
      {selectedOfferedSemesters && selectedOfferedSemesters.map((semester) => (
         <div key={`offered-${semester}`} className="filter-tag" style={{ backgroundColor: "#999" }}>
             <button onClick={() => removeOfferedSemester(semester)}><b>×</b></button>
             {semester}
         </div>
      ))}
      {/* Then render the other selected filters */}
      {Object.entries(selectedFilters).map(([major, filters]) =>
        filters.map((filter) => {
            // 🛠 Ensure the filter is formatted before splitting
            const formattedFilter = filter.replace(/^[^-]+---/, "").replace(/---/g, " → ");

            // Split by `→` and get the last two parts
            const filterParts = formattedFilter.split(" → ");
            const displayedFilter = filterParts.slice(-2).join(" → "); // Keep only last 2 parts

            return (
            <div
                key={`${major}-${filter}`}
                className="filter-tag"
                style={{ backgroundColor: majorColors[major] || "gray" }}
            >
                <button onClick={() => handleFilterChange(major, filter)}><b>×</b></button>
                {displayedFilter} {/* ✅ Display only last two segments */}
            </div>
            );
        })
        )}

    </div>
  );
};

export default SelectedFilters;
