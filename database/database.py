from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os

# Configure the PostgreSQL database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:565675678@localhost:5432/gened_db")

# Create the database engine
engine = create_engine(DATABASE_URL, echo=True)

# Create a configured session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to initialize the database
def init_db():
    """Creates database tables based on SQLAlchemy models."""
    Base.metadata.create_all(engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    init_db()
