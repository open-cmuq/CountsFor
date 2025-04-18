import React, { useState, useRef, useEffect } from "react";

const SingleSelectDropdown = ({ options = [], selected, onChange, major = "" }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  const displayMap = {
    all: "All Courses",
    with: "Has Pre-reqs",
    without: "No Pre-reqs",
  };

  const handleSelect = (value) => {
    onChange(value);
    setIsOpen(false);
  };

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className={`dropdown cell-container ${major === "prereq" ? "dropdown-prereq" : ""}`} ref={dropdownRef}>
      <button className="dropdown-btn" onClick={() => setIsOpen(!isOpen)}>
        Select
      </button>
      {isOpen && (
        <div className="dropdown-content">
        {options.map((opt) => (
        <label key={opt} className="dropdown-item" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <input
            type="checkbox"
            name="prereq-dropdown"
            checked={selected === opt}
            onChange={() => handleSelect(opt)}
            />
            {displayMap[opt] || opt}
        </label>
        ))}
        </div>
      )}
    </div>
  );
};

export default SingleSelectDropdown;
