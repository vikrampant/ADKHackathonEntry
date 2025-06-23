import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from routes.landing import router as landing_router
from routes.jobreq import router as jobreq_router
from routes.candidate import router as candidate_router
from util import AGENT_DIR, ADK_SESSION_DATABASE_URL
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.sessions import DatabaseSessionService

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.join(BASE_DIR, "agents")

print("AGENT_DIR: " + AGENT_DIR)
print("ADK_SESSION_DATABASE_URL: " + ADK_SESSION_DATABASE_URL)

#app = FastAPI()
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    # session_service_uri=ADK_SESSION_DATABASE_URL,
    allow_origins=["*"],
    web=False
)
app.include_router(landing_router)
app.include_router(jobreq_router)
app.include_router(candidate_router)

load_dotenv()

# Create and store session service in app.state
session_service = DatabaseSessionService(ADK_SESSION_DATABASE_URL)
app.state.session_service = session_service

if __name__ == "__main__":
    print("Starting FastAPI server ...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9999,
        reload=False
    )