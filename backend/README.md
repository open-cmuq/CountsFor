## **📌 Project Structure**

* The backend follows a **layered architecture** to ensure clean separation of concerns:

</svg></button></span></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="!whitespace-pre"><span>backend/
│── app/
│   ├── routers/        # API route definitions (FastAPI endpoints)
│   │   ├── courses.py  # Course-related endpoints
│   ├── schemas.py      # Pydantic models for request validation & response formatting
│── database/
│   ├── models.py       # SQLAlchemy ORM models for database tables
│   ├── db.py           # Database connection setup
│── repository/
│   ├── courses.py      # Data access layer (queries to the database)
│── services/
│   ├── courses.py      # Business logic layer (processing fetched data)
│── main.py             # FastAPI app entry point  </span></code></div></div></pre>

## **⚙️ Layered Architecture Explained**

The backend is designed with  **three layers** :

1. **🔗 API Layer (`routers/`)**
   * Exposes REST API endpoints using  **FastAPI** .
   * Calls the **service layer** for business logic.
   * Ensures validation using  **Pydantic schemas** .
2. **⚙️ Service Layer (`services/`)**
   * Implements **business logic** (e.g., structuring responses, processing data).
   * Calls the **repository layer** for data access.
   * Ensures consistency and formatting before returning responses.
3. **🗄️ Repository Layer (`repository/`)**
   * Directly interacts with the **database** using  **SQLAlchemy** .
   * Contains **raw queries** and fetches data  **without processing it** .
   * Called by the **service layer** to retrieve structured data.

## ** Running the Backend**

### **Run FastAPI Server**

Start the server with:
</svg></button></span></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="!whitespace-pre language-sh"><span>uvicorn backend.app.main:app --reload
</span></code></div></div></pre>

The API will be available at:
</svg></button></span></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="!whitespace-pre"><span>http://127.0.0.1:8000</span></code></div></div></pre>
