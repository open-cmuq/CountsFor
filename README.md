# CountsFor

Welcome to the **CountsFor** repository! This project provides a web application designed to assist CMUQ faculty in analyzing and planning courses that fulfill requirements across the four majors at CMU-Q. It includes a backend for data processing and API, a frontend interface, and analytics components.

---

## Deployment

The live application can be accessed at:

*   **URL:** [https://countsfor.qatar.cmu.edu/](https://countsfor.qatar.cmu.edu/)
*   **Access:** Requires connection to the CMU VPN.

Maintainers can find detailed instructions on how to redeploy updates in the [`DEPLOYMENT.md`](DEPLOYMENT.md) file.

---

## Getting Started

### Prerequisites

*   Git
*   Python (3.8+ recommended)
*   Node.js (16+ recommended)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd CountsFor # Or your cloned directory name
    ```
2.  **Set up the Backend:** Follow the detailed setup instructions in `backend/README.md`.
3.  **Set up the Frontend:** Follow the detailed setup instructions in `frontend/README.md`.

## Project Structure

The project is organized into the following main directories:

*   **`backend/`**: Contains the FastAPI backend application, including API routers, services, database interactions, and data processing scripts. See `backend/README.md` for details.
*   **`frontend/`**: Contains the frontend application code (e.g., React, Vue, Angular). See `frontend/README.md` for details.
*   **`data/`**: Holds raw and processed data used by the application (e.g., audit info, course details, enrollment data).
*   **`database/`**: Contains database configurations, models (`models.py`), and potentially migration files. Note: The actual database file (`gened.db`) might be located elsewhere depending on setup.
*   **`analytics/`**: Includes scripts for data analysis and potential predictive modeling.
*   **`tests/`**: Contains tests for different parts of the application. See `tests/README.md`.

## Running the Application

1.  **Run the Backend Server:** Navigate to the `backend` directory and follow the instructions in `backend/README.md`. Typically involves running `uvicorn`.
2.  **Run the Frontend Development Server:** Navigate to the `frontend` directory and follow the instructions in `frontend/README.md`. Typically involves running `npm start` or `yarn dev`.

## Running Tests

*   **Backend:** Navigate to the project root directory and run tests using `pytest`. See `tests/README.md` for detailed instructions.
    ```bash
    # Ensure you are in the project root directory (GenEd-CMUQ)
    python -m pytest tests
    ```
*   **Frontend:** Navigate to the `frontend` directory and follow the testing instructions in `frontend/README.md`.

## Contribution Guidelines

### Creating a Branch
Before making any changes, create a new branch based on the feature or fix you are working on:
```bash
git checkout -b feature-name

## Examples

```bash
git checkout -b add-enrollment-prediction-model
git checkout -b add-front-end-compenents
```

### Committing Changes
Follow a structured commit message format:

```bash
git commit -m "Fix: Improved course extraction logic"
```

### Commit Message Conventions
- **Feat:** for new features
- **Fix:** for bug fixes
- **Refactor:** for code improvements
- **Docs:** for documentation updates

### Pushing to GitHub
Once changes are committed, push the branch:

```bash
git push origin feature-name
```

### Creating a Pull Request (PR)
- Open a **Pull Request (PR)** on **GitHub**.
- Add **Boushra Bendou** and the other team member as **reviewers**.
- Provide a **clear description** of what changes were made.
- Ensure that **tests pass** before requesting a merge.

### Code Review & Merging
- At least **one reviewer must approve** the PR before merging.
- After approval, **merge the branch using the GitHub UI**.
- **Never push directly to `main`!** Always use branches and PRs.

### Keeping Your Branch Updated
If your branch is behind `main`, update it before merging:

```bash
git checkout main
git pull origin main
git checkout feature-name
git merge main
```

## Best Practices
✔ **Keep code modular and well-documented.**
✔ **Follow consistent naming conventions.**
✔ **Use environment variables for sensitive data.**
✔ **Run tests before pushing code.**
✔ **Write meaningful commit messages.**
