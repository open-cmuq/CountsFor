"""
this script handles database connection setup and session management.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.models import Base

# Load database URL (Default: SQLite)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///backend/database/gened_db.sqlite")

# Add these lines for debugging
db_file_path = DATABASE_URL.replace("sqlite:///", "")
print(f"\n--- !!! BACKEND USING DATABASE FILE: {os.path.abspath(db_file_path)} !!! ---\n")
# End of added lines

# Create the engine (Enable echo temporarily for debugging)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=True)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Provides a database session dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Creates all database tables based on SQLAlchemy models."""
    Base.metadata.create_all(engine)
    print("✅ Database tables created successfully.")

def reset_db():
    """Drops all tables and recreates them."""
    Base.metadata.drop_all(engine)
    print("🗑️  All tables dropped.")

    Base.metadata.create_all(engine)
    print("✅ Database reset and tables recreated.")
