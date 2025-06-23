import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set up application database
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/sqlite.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Set up ADK session database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.join(BASE_DIR, "agents")
ADK_SESSION_DATABASE_URL = f"sqlite:///./src/agents/session.db"
