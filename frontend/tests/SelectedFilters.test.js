/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SelectedFilters from '../src/components/SelectedFilters.js';

describe('SelectedFilters', () => {
  const mockHandleFilterChange = jest.fn();
  const mockRemoveOfferedSemester = jest.fn();

  beforeEach(() => {
    mockHandleFilterChange.mockClear();
    mockRemoveOfferedSemester.mockClear();
  });

  test('renders offered semesters and calls removeOfferedSemester on click', () => {
    render(
      <SelectedFilters
        selectedFilters={{ BA: [], BS: [], CS: [], IS: [] }}
        selectedOfferedSemesters={['F23', 'S24']}
        handleFilterChange={mockHandleFilterChange}
        removeOfferedSemester={mockRemoveOfferedSemester}
      />
    );

    expect(screen.getByText('F23')).toBeInTheDocument();
    expect(screen.getByText('S24')).toBeInTheDocument();

    const closeBtn = screen.getAllByRole('button')[0];
    fireEvent.click(closeBtn);

    expect(mockRemoveOfferedSemester).toHaveBeenCalledWith('F23');
  });

  test('renders requirement filters and calls handleFilterChange on X click', () => {
    render(
      <SelectedFilters
        selectedFilters={{
          IS: ['BS in Information Systems---Concentration---Information Security and Privacy---Regulatory and Behavioral Core'],
          CS: ['GenEd---Science and Engineering---Science and Engineering (CB)---Lab Requirement']
        }}
        selectedOfferedSemesters={[]}
        handleFilterChange={mockHandleFilterChange}
        removeOfferedSemester={mockRemoveOfferedSemester}
      />
    );

    expect(screen.getByText('Information Security and Privacy → Regulatory and Behavioral Core')).toBeInTheDocument();
    const matches = screen.getAllByText((content, element) =>
        element?.textContent.includes('Lab Requirement')
      );
      expect(matches.length).toBeGreaterThan(0);
      
      
    const closeButtons = screen.getAllByRole('button');
    fireEvent.click(closeButtons[0]);

    expect(mockHandleFilterChange).toHaveBeenCalledWith('IS', 'BS in Information Systems---Concentration---Information Security and Privacy---Regulatory and Behavioral Core');
  });

  test('returns null when there are no selected filters or semesters', () => {
    render(
      <SelectedFilters
        selectedFilters={{ BA: [], BS: [], CS: [], IS: [] }}
        selectedOfferedSemesters={[]}
        handleFilterChange={mockHandleFilterChange}
        removeOfferedSemester={mockRemoveOfferedSemester}
      />
    );

    expect(screen.queryByTestId('selected-filters')).not.toBeInTheDocument();
  });
});
