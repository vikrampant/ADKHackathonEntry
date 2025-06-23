import uuid
import asyncio
import re
import time
from google.genai import types
import json
from fastapi import HTTPException
from typing import Optional
from sqlalchemy.orm import Session
from models.jobreq import JobReq
from util import SessionLocal
from models.schemas.jobreq_schema import JobReqRequest, JobReqResponse
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from agents.candidate_agent.agent import CandidateAgentOrchestrator

# Constants
APP_NAME = "candidate_agent"

# Step 1: Create Your Async Function
async def process_resume_content_for_job(job_id: str, resume_content: str, session_service: Optional[DatabaseSessionService] = None):
    """
    Async function that runs after jobreq is created
    This is where you can add your async processing logic
    """
    print(f"🚀 Starting async processing for job {job_id}")
    print(f"📋 Resume Content: {resume_content[:100]}")

    # Step 2: Run Sequential Agent
    await run_sequential_agents(job_id, resume_content, session_service)
    
    print(f"✅ Async processing completed for jobreq {job_id}")


async def run_sequential_agents(job_id: str, resume_content: str, session_service: Optional[DatabaseSessionService] = None):
    """
    Run sequential agents for candidate
    """
    print(f"🚀 Running sequential agents for candidate {job_id}")
   
    request_body = {
        "job_id": job_id,
        "resume_content": resume_content,
    }

    # Build session variables for agent call
    unique_id = str(uuid.uuid4())
    session_id = unique_id
    user_id = "default_user"  # Replace with actual user ID logic if needed
    print("Session ID = " + session_id)
    print("User ID = " + user_id)

    try:
        # Check if session_service is provided
        if session_service is None:
            print("❌ Session service not provided")
            return
        
        # Build initial session state
        initial_state = {
            "job_id": job_id,
            "resume_content": resume_content,
        }

        # Create session
        current_session = None
        try:
            current_session = await session_service.get_session(
                app_name=APP_NAME,
                session_id=session_id,
                user_id=user_id,
            )
            if current_session is not None:
                current_session.state = initial_state
        except Exception as e:
            print(f"Error retrieving session: {e}")

        # If no session found, creating new session
        if current_session is None:
            current_session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id,
                state=initial_state,
            )
        else:
            print(f"Existing session '{session_id}'has been found. Resuming session.")

        # print("Current session = " + str(current_session))

        # Initialize the candidate agent orchestrator
        candidate_agent = CandidateAgentOrchestrator()

        # Initialize the ADK Runner with our multi-agent pipeline
        runner = Runner(
            app_name=APP_NAME,
            agent=candidate_agent.root_agent,
            session_service = session_service,
        )
        
        print("After initializing the runner")

        # Format the user query as a structured message using the google genais content types
        user_message = types.Content(
            role="user", parts=[types.Part.from_text(text=json.dumps({
                "job_id": request_body["job_id"],
                "resume_content": request_body["resume_content"],
            }))]
        )

        print("Before running the agent asynchronously")

        # Run the agent asynchronously
        events = runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message,
        )

        print("After running the agent")

        # Process events to find the final response
        final_response = None
        last_event_content = None
        async for event in events:
            if event.is_final_response():
                if event.content and event.content.parts:
                    last_event_content = event.content.parts[0].text

        if last_event_content:
            final_response = last_event_content
        else:
            print("No final response event found from the Sequential Agent.")

        # Parse the JSON response from agents
        if final_response is None:
            raise HTTPException(status_code=500, detail="No response received from agent.")

        # Clean up Markdown code block if it exists
        # This handles responses like: ```json\n{ ... }\n```
        cleaned_response = re.sub(r"^```(?:json)?\n|```$", "", final_response.strip(), flags=re.IGNORECASE)

        # Loading the cleaned JSON
        try:
            response_data = json.loads(cleaned_response)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Agent response is not valid JSON.")

        print("==== Session Event Exploration ====")
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

        # Log final Session state
        print("=== Final Session State ===")
        if session and hasattr(session, 'state'):
            for key, value in session.state.items():
                print(f"{key}: {value}")

        # Return the structured response using your Pydantic model
        return {
            "candidate_location_review_response": response_data.get("candidate_location_review_response", ""),
        } 

        print(f"✅ Sequential agents completed for candidate {job_id}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process agent query: {e}")

