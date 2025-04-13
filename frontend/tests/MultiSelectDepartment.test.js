/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import MultiSelectDepartment from '../src/components/MultiSelectDepartment.js';

describe('MultiSelectDepartment', () => {
  const departmentsMock = [
    { dep_code: '76', name: 'English' },
    { dep_code: '21', name: 'Mathematics' },
  ];
  const mockSetSelected = jest.fn();

  beforeEach(() => {
    mockSetSelected.mockClear();
  });

  test('renders button and toggles dropdown', () => {
    render(
      <MultiSelectDepartment
        departments={departmentsMock}
        selectedDepartments={[]}
        setSelectedDepartments={mockSetSelected}
      />
    );

    const toggleBtn = screen.getByText(/choose departments/i);
    expect(toggleBtn).toBeInTheDocument();

    fireEvent.click(toggleBtn);
    expect(screen.getByText(/select all/i)).toBeInTheDocument();
  });

  test('selects a department when checkbox is clicked', () => {
    render(
      <MultiSelectDepartment
        departments={departmentsMock}
        selectedDepartments={[]}
        setSelectedDepartments={mockSetSelected}
      />
    );

    fireEvent.click(screen.getByText(/choose departments/i)); 

    const checkbox = screen.getByLabelText(/76 - English/i);
    fireEvent.click(checkbox);

    expect(mockSetSelected).toHaveBeenCalledWith([
      { dep_code: '76', name: 'English' },
    ]);
  });

  test('calls setSelectedDepartments with all departments when SELECT ALL is clicked', () => {
    render(
      <MultiSelectDepartment
        departments={departmentsMock}
        selectedDepartments={[]}
        setSelectedDepartments={mockSetSelected}
      />
    );

    fireEvent.click(screen.getByText(/choose departments/i));
    fireEvent.click(screen.getByLabelText(/select all/i));

    expect(mockSetSelected).toHaveBeenCalledWith(departmentsMock);
  });

  test('clears selected departments when "Clear Selection" is clicked', () => {
    render(
      <MultiSelectDepartment
        departments={departmentsMock}
        selectedDepartments={[{ dep_code: '76', name: 'English' }]}
        setSelectedDepartments={mockSetSelected}
      />
    );

    fireEvent.click(screen.getByText(/1 selected/i));
    fireEvent.click(screen.getByText(/clear selection/i));

    expect(mockSetSelected).toHaveBeenCalledWith([]);
  });

  test('closes dropdown when clicking outside', () => {
    render(
      <>
        <MultiSelectDepartment
          departments={departmentsMock}
          selectedDepartments={[]}
          setSelectedDepartments={mockSetSelected}
        />
        <div data-testid="outside-element">Outside</div>
      </>
    );

    fireEvent.click(screen.getByText(/choose departments/i));
    expect(screen.getByText(/select all/i)).toBeInTheDocument();
  
    fireEvent.mouseDown(screen.getByTestId('outside-element'));

    expect(screen.queryByText(/select all/i)).not.toBeInTheDocument();
  });

  test('deselects a department when checkbox is unchecked', () => {
    render(
      <MultiSelectDepartment
        departments={departmentsMock}
        selectedDepartments={[{ dep_code: '76', name: 'English' }]}
        setSelectedDepartments={mockSetSelected}
      />
    );
  
    fireEvent.click(screen.getByText(/1 selected/i));
    const checkbox = screen.getByLabelText(/76 - English/i);
    fireEvent.click(checkbox); // uncheck
  
    expect(mockSetSelected).toHaveBeenCalledWith([]);
  });

  test('"SELECT ALL" is not checked when not all departments are selected', () => {
    render(
      <MultiSelectDepartment
        departments={departmentsMock}
        selectedDepartments={[{ dep_code: '76', name: 'English' }]}
        setSelectedDepartments={mockSetSelected}
      />
    );
  
    fireEvent.click(screen.getByText(/1 selected/i));
    const selectAllCheckbox = screen.getByLabelText(/select all/i);
    expect(selectAllCheckbox).not.toBeChecked();
  });
  
  
});
