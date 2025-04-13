/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import EnrollmentAnalytics from '../src/components/Analytics';
import '@testing-library/jest-dom';

// Mock Plotly
jest.mock('react-plotly.js', () => (props) => {
  return (
    <div data-testid="mock-plot">
      Plotly Graph: {props.layout?.title}
    </div>
  );
});

// Mock fetch
beforeAll(() => {
  global.fetch = jest.fn((url) => {
    if (url.includes('76-101')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          enrollment_data: [
            { semester: 'F22', enrollment_count: 25, class_: 1 },
            { semester: 'S23', enrollment_count: 30, class_: 2 },
          ],
        }),
      });
    }
    return Promise.reject(new Error('Unknown endpoint: ' + url));
  });
});

afterAll(() => {
  global.fetch.mockRestore();
});

describe('EnrollmentAnalytics', () => {
  test('renders input fields and buttons', () => {
    render(<EnrollmentAnalytics />);
    expect(screen.getAllByPlaceholderText(/enter course code/i)).toHaveLength(2);
    expect(screen.getByText(/add course/i)).toBeInTheDocument();
    expect(screen.getByText(/load course/i)).toBeInTheDocument();
  });

  test('fetches and displays aggregated enrollment plot', async () => {
    render(<EnrollmentAnalytics />);
    const input = screen.getAllByPlaceholderText(/enter course code/i)[0];
    fireEvent.change(input, { target: { value: '76-101' } });
    fireEvent.click(screen.getByText(/add course/i));

    await waitFor(() => {
      const plots = screen.getAllByTestId('mock-plot');
      expect(plots.some(p => p.textContent.includes("Aggregated Enrollment Over Semesters"))).toBe(true);
    });
  });

  test('fetches and displays class-based enrollment plot', async () => {
    render(<EnrollmentAnalytics />);
    const input = screen.getAllByPlaceholderText(/enter course code/i)[1];
    fireEvent.change(input, { target: { value: '76-101' } });
    fireEvent.click(screen.getByText(/load course/i));

    await waitFor(() => {
      const plots = screen.getAllByTestId('mock-plot');
      expect(plots.some(p => p.textContent.includes("Enrollment for 76-101"))).toBe(true);
    });
  });
});
