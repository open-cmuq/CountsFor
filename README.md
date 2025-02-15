# GenEd-CMUQ

Welcome to the **GenEd-CMUQ** repository! This project is designed to create a website support CMUQ faculty analyze and plan courses that fulfill requirements across the four majors at CMU-Q . The repo includes backend data processing, database management, backend, analytics and a frontend interface.

---

## 📁 Folder Structure

### **1️⃣ `backend/`** - Backend logic and scripts for data extraction, processing, and database interaction.
   - **`app/`** → Contains the core backend logic, including:
     - `database.py` → Manages database connections and schema.
     - `models.py` → Defines database models using SQLAlchemy.
     - `schemas.py` → Defines Pydantic schemas for data validation.
     - `main.py` → Entry point for the backend API.
   - **`scripts/`** → Contains utility scripts for extracting and populating data.
     - `extract_audit_data.py` → Extracts audit requirements from JSON files.
     - `extract_course_data.py` → Extracts course data from structured JSON files.
     - `extract_enrollment_data.py` → Extracts enrollment data.
     - `populate_courses.py` → Populates the database with course data (in progress).
   - **`tests/`** → Contains unit tests for backend functionality.

### **2️⃣ `data/`** - Raw + postproccessed data storage for audit, course, and enrollment information.
   - **`audit/`** → Degree audit JSON files + clean audit dataset.
   - **`course/`** → Course metadata stored as JSON files + clean course dataset.
   - **`enrollment/`** → Clean enrollment dataset.

### **3️⃣ `database/`** - Contains database-related configurations.
   - **`migrations/`** → Migration files for database schema changes.
   - **`gened.db`** → The PostgreSQL database file.

### **4️⃣ `frontend/`** - Contains frontend code for user interaction.
   - **`public/`** → Static assets for the frontend (in progress).
   - **`src/`** → Source code for frontend components (in peogress).

### **5️⃣ `analytics/`** - Scripts for data analysis and predictive modeling.
   - **`predict_next_sem.py`** → A script for predicting course demand for the next semester.

---

## 🚀 Contribution Guidelines

### **1️⃣ Creating a Branch**
Before making any changes, create a new branch based on the feature or fix you are working on:
```bash
git checkout -b feature-name

## 📝 Examples

```bash
git checkout -b add-enrollment-prediction-model
git checkout -b add-front-end-compenents
```

---

## 2️⃣ Committing Changes
Follow a structured commit message format:

```bash
git commit -m "Fix: Improved course extraction logic"
```

### **Commit Message Conventions**
- **Feat:** for new features  
- **Fix:** for bug fixes  
- **Refactor:** for code improvements  
- **Docs:** for documentation updates  

---

## 3️⃣ Pushing to GitHub
Once changes are committed, push the branch:

```bash
git push origin feature-name
```

---

## 4️⃣ Creating a Pull Request (PR)
- Open a **Pull Request (PR)** on **GitHub**.
- Add **Boushra Bendou** and the other team member as **reviewers**.
- Provide a **clear description** of what changes were made.
- Ensure that **tests pass** before requesting a merge.

---

## 5️⃣ Code Review & Merging
- At least **one reviewer must approve** the PR before merging.
- After approval, **merge the branch using the GitHub UI**.
- 🚨 **Never push directly to `main`!** Always use branches and PRs.

---

## 6️⃣ Keeping Your Branch Updated
If your branch is behind `main`, update it before merging:

```bash
git checkout main
git pull origin main
git checkout feature-name
git merge main
```

---

## 📌 Best Practices
✔ **Keep code modular and well-documented.**  
✔ **Follow consistent naming conventions.**  
✔ **Use environment variables for sensitive data.**  
✔ **Run tests before pushing code.**  
✔ **Write meaningful commit messages.**  
