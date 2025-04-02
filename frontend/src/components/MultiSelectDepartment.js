import React, { useState, useRef, useEffect } from "react";

const MultiSelectDepartment = ({ departments = [], selectedDepartments, setSelectedDepartments }) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);
  
    useEffect(() => {
      function handleClickOutside(event) {
        if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
          setIsOpen(false);
        }
      }
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);
  
    const toggleDropdown = () => setIsOpen(!isOpen);
  
    const handleSelectAll = () => {
      setSelectedDepartments(selectedDepartments.length === departments.length ? [] : [...departments]);
    };
  
    return (
      <div className="search cell-container" ref={dropdownRef}>
        <button className="dropdown-btn" onClick={toggleDropdown}>
          {selectedDepartments.length > 0 ? `${selectedDepartments.length} Selected` : "Choose Departments"} ▼
        </button>
  
        {isOpen && (
          <div className="dropdown-content">
            <label className="dropdown-item">
              <input type="checkbox" checked={selectedDepartments.length === departments.length} onChange={handleSelectAll} />
              <strong>SELECT ALL</strong>
            </label>
  
            {departments.map((dept) => (
              <label key={dept.dep_code} className="dropdown-item">
                <input
                  type="checkbox"
                  checked={selectedDepartments.some(selected => selected.dep_code === dept.dep_code)}
                  onChange={(e) => {
                    const updatedSelection = e.target.checked
                      ? [...selectedDepartments, dept]
                      : selectedDepartments.filter(d => d.dep_code !== dept.dep_code);
  
                    setSelectedDepartments(updatedSelection);
                  }}
                />
                {dept.dep_code} - {dept.name}
              </label>
            ))}
  
            <button className="clear-btn" onClick={() => setSelectedDepartments([])}>Clear Selection</button>
          </div>
        )}
      </div>
    );
  };
  
  export default MultiSelectDepartment;
  
  
  
  