from sqlalchemy import create_engine
from jobreq import Base

DATABASE_URL = "sqlite:///../../data/sqlite.db"  # Adjust path as needed
engine = create_engine(DATABASE_URL, echo=True)

# Create all tables defined by Base subclasses
Base.metadata.create_all(engine) 