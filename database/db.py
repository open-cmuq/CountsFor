"""
this script is used to create the database tables based on the SQLAlchemy models.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/gened_db.sqlite")

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def drop_db():
    """Drops all database tables."""
    Base.metadata.drop_all(engine)
    print("Database tables dropped successfully.")

def init_db():
    """Creates database tables based on SQLAlchemy models."""
    Base.metadata.create_all(engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    drop_db()  # Drop existing tables
    init_db()  # Recreate tables
