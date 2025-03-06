import React from "react";

const SearchBar = ({ departments, selectedDepartment, setSelectedDepartment, searchQuery, setSearchQuery }) => {
  const handleClearSearch = () => {
    setSearchQuery("");
    setSelectedDepartment("");
  };

  return (
    <div className="search-container">
      <label className="search-label">SEARCH</label>
      <div className="search-inputs">
        <select 
          value={selectedDepartment} 
          onChange={(e) => setSelectedDepartment(e.target.value)}
          className="dropdown"
        >
          <option value="">Choose a department</option>
          {departments.map((dept) => (
            <option key={dept} value={dept}>{dept}</option>
          ))}
        </select>
        <input
          type="text"
          placeholder="Specific course number"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="text-input"
        />
        <button className="search-btn">🔍</button>
        <button onClick={handleClearSearch} className="search-clear-btn">CLEAR SEARCH</button>
      </div>

      {(selectedDepartment || searchQuery) && (
        <div className="selected-filters">
          {selectedDepartment && (
            <span className="filter-tag">
              {selectedDepartment} <button onClick={() => setSelectedDepartment("")}>×</button>
            </span>
          )}
          {searchQuery && (
            <span className="filter-tag">
              {searchQuery} <button onClick={() => setSearchQuery("")}>×</button>
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchBar;
