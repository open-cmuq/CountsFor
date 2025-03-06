import React from "react";

const SelectedFilters = ({ selectedFilters, handleFilterChange }) => {
  const majorColors = {
    BA: "#4A68FB",  
    BS: "#22AA0A",  
    CS: "#CF1314",  
    IS: "#FFC033", 
  };
  
  return (
    Object.keys(selectedFilters).some((major) => selectedFilters[major].length > 0) && (
      <div className="selected-filters">
        {Object.entries(selectedFilters).map(([major, filters]) =>
          filters.map((filter) => (
            <div
              key={`${major}-${filter}`}
              className="filter-tag"
              style={{ backgroundColor: majorColors[major] || "gray" }} // Fallback to gray if major not found
            >
              {filter}
              <button onClick={() => handleFilterChange(major, filter)}>✖</button>
            </div>
          ))
        )}
      </div>
    )
  );
};

export default SelectedFilters;
