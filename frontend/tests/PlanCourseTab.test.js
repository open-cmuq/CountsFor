/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import PlanCourseTab from '../src/components/PlanCourseTab';
import '@testing-library/jest-dom';

// Mock localStorage
beforeEach(() => {
  const store = {};
  jest.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => store[key] || null);
  jest.spyOn(Storage.prototype, 'setItem').mockImplementation((key, value) => {
    store[key] = value;
  });
});

// Mock fetch
beforeAll(() => {
  global.fetch = jest.fn((url) => {
    if (url.includes('/requirements')) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            requirements: [
              {
                requirement:
                  'BS in Information Systems---Concentration---Information Security and Privacy---Regulatory and Behavioral Core',
                type: false,
                major: 'is',
              },
              {
                requirement:
                  'GenEd---Science and Engineering---Science and Engineering (CB)---Lab Requirement',
                type: true,
                major: 'cs',
              },
            ],
          }),
      });
    }

    if (url.includes('/courses/search?searchQuery=76-101')) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            courses: [
              {
                course_code: '76-101',
                course_name: 'Interpretation & Argument',
              },
            ],
          }),
      });
    }

    if (url.includes('/courses/76-101')) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            course_code: '76-101',
            course_name: 'Interpretation & Argument',
            offered: ['F23', 'S24'],
            prerequisites: '[76-100]',
            requirements: {
              IS: [
                {
                  requirement:
                    'BS in Information Systems---Concentration---Information Security and Privacy---Regulatory and Behavioral Core',
                  type: false,
                },
              ],
              CS: [
                {
                  requirement:
                    'GenEd---Science and Engineering---Science and Engineering (CB)---Lab Requirement',
                  type: true,
                },
              ],
            },
          }),
      });
    }

    return Promise.reject(new Error('Unknown endpoint: ' + url));
  });
});

afterAll(() => {
  global.fetch.mockRestore();
});

describe('PlanCourseTab', () => {
  test('renders title and subtitle', () => {
    render(<PlanCourseTab />);
    expect(screen.getByText(/Plan Courses/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Add courses from the main table or search to build/i)
    ).toBeInTheDocument();
  });

  test('searches and adds a course to the plan', async () => {
    render(<PlanCourseTab />);
    const input = screen.getByPlaceholderText(/Search by course code/i);
    fireEvent.change(input, { target: { value: '76-101' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

    await screen.findByText(/76-101/i);
    fireEvent.click(screen.getByText('+ Add'));

    await screen.findByText(/Course added! 🎉/i);
  });

  test('prevents duplicate addition', async () => {
    render(<PlanCourseTab />);
    const input = screen.getByPlaceholderText(/Search by course code/i);
    fireEvent.change(input, { target: { value: '76-101' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
  
    await screen.findByText('+ Add');
    fireEvent.click(screen.getByText('+ Add'));
  
    // Wait for the toast AND the button to change
    const buttons = await screen.findAllByText(/Added/i);
    const addedButton = buttons.find((btn) => btn.tagName === 'BUTTON');
    expect(addedButton).toBeInTheDocument();
  
    fireEvent.click(addedButton);
    expect(await screen.findByText(/Course already added! 😅/i)).toBeInTheDocument();
  });  
  
  test('clears all courses when confirmed', async () => {
    window.confirm = jest.fn(() => true);
    render(<PlanCourseTab />);
  
    const input = screen.getByPlaceholderText(/Search by course code/i);
    fireEvent.change(input, { target: { value: '76-101' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
  
    await screen.findByText('+ Add');
    fireEvent.click(screen.getByText('+ Add'));
  
    const table = screen.getByRole('table');
    const courseCell = await within(table).findByText('76-101');
    expect(courseCell).toBeInTheDocument();
  
    fireEvent.click(screen.getByText(/Clear All/i));
  
    await waitFor(() => {
      expect(within(table).queryByText('76-101')).not.toBeInTheDocument();
    });
  });
});