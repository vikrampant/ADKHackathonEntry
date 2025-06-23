import uuid
import asyncio
import re
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
from agents.job_req_agent import JobReqAgentOrchestrator

# Constants
APP_NAME = "jobreq_agent"

def create_jobreq(jobreq_data: dict):
    db = SessionLocal()
    jobreq_data['job_id'] = str(uuid.uuid4())
    # Set default approval status if not provided
    if 'job_approval_status' not in jobreq_data or jobreq_data['job_approval_status'] is None:
        jobreq_data['job_approval_status'] = "pending"
    jobreq = JobReq(**jobreq_data)
    db.add(jobreq)
    db.commit()
    db.refresh(jobreq)
    return jobreq

def get_jobreq(job_id: str):
    db = SessionLocal()
    jobreq = db.query(JobReq).filter(JobReq.job_id == job_id).first()
    db.close()
    return jobreq

def update_jobreq(job_id: str, **kwargs):
    db = SessionLocal()
    try:
        jobreq = db.query(JobReq).filter(JobReq.job_id == job_id).first()
        if not jobreq:
            raise HTTPException(status_code=404, detail="Job request not found")
        
        # Update only provided fields
        for field, value in kwargs.items():
            if hasattr(jobreq, field) and value is not None:
                setattr(jobreq, field, value)
        
        db.commit()
        db.refresh(jobreq)
        return jobreq
    finally:
        db.close()

# Step 1: Create Your Async Function
async def process_jobreq_after_creation(job_id: str, job_title: str, session_service: Optional[DatabaseSessionService] = None):
    """
    Async function that runs after jobreq is created
    This is where you can add your async processing logic
    """
    print(f"🚀 Starting async processing for jobreq {job_id}")
    print(f"📋 Job Title: {job_title}")

    # Step 2: Run Sequential Agent
    await run_sequential_agents(job_id, job_title, session_service)
    
    # # Example 1: Simulate sending email notification
    # await send_email_notification(job_id, job_title)
    
    print(f"✅ Async processing completed for jobreq {job_id}")

# Example async functions you can implement:
# async def send_email_notification(job_id: str, job_title: str):
#     """Simulate sending email notification"""
#     print(f"📧 Sending email notification for jobreq {job_id}")
#     # Simulate async email sending
#     await asyncio.sleep(1)
#     print(f"✅ Email sent for jobreq {job_id}")

async def run_sequential_agents(job_id: str, job_title: str, session_service: Optional[DatabaseSessionService] = None):
    """
    Run sequential agents for jobreq
    """
    print(f"🚀 Running sequential agents for jobreq {job_id}")
   
    # Get the jobreq from the database
    jobreq = get_jobreq(job_id)
    
    # Check if jobreq exists
    if jobreq is None:
        print(f"❌ Job request with ID {job_id} not found")
        return

    # Build the request body
    request_body = jobreq
    print("Processing job request with the following details:")
    print("Job title = " + request_body.job_title)

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
            "job_experience_level": jobreq.job_experience_level,
            "job_title": job_title,
            "revised_job_title": "",            
            "job_description": jobreq.job_description,
            "job_description_analysis": "",
            "job_description_recommended": "",
            "job_type": jobreq.job_type,
            "job_approval_status": jobreq.job_approval_status,
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

        # Initialize the jobreq agent orchestrator
        jobreq_agent = JobReqAgentOrchestrator()

        # Initialize the ADK Runner with our multi-agent pipeline
        runner = Runner(
            app_name=APP_NAME,
            agent=jobreq_agent.root_agent,
            session_service = session_service,
        )
        
        # print("After initializing the runner")

        # Format the user query as a structured message using the google genais content types
        user_message = types.Content(
            role="user", parts=[types.Part.from_text(text=json.dumps({
                "job_id": request_body.job_id,
                "job_approval_status": "pending",  # Initial status, will be updated by the agent
                "job_experience_level": request_body.job_experience_level,
                "job_title": request_body.job_title,
                "job_description": request_body.job_description,
                "job_type": request_body.job_type,
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


        # Prepare context for the template
        # context = {
        #     "request": request,
        #     "jobreq": JobReqResponse(
        #         job_id=response_data.get("job_id", ""),
        #         job_experience_level=response_data.get("job_experience_level", ""),
        #         job_title=response_data.get("job_title", ""),
        #         revised_job_title=response_data.get("revised_job_title", ""),
        #         job_description=response_data.get("job_description", ""),
        #         job_description_analysis=response_data.get("job_description_analysis", ""),
        #         job_description_recommended=response_data.get("job_description_recommended", ""),
        #         job_type=response_data.get("job_type", ""),
        #         job_approval_status=response_data.get("job_approval_status", ""),
        #         job_approval_status_tracker_id=response_data.get("job_approval_status_tracker_id", ""),
        #         job_approval_status_notes_by_approver=response_data.get("job_approval_status_notes_by_approver", "")
        #     )
        # }

        print("==== Session Event Exploration ====")
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

        # Log final Session state
        print("=== Final Session State ===")
        if session and hasattr(session, 'state'):
            for key, value in session.state.items():
                print(f"{key}: {value}")

        # Update the jobreq in the database with AI processing results
        print("🔄 Updating job request in database...")
        try:
            update_data = {}
            
            # Update job title if AI provided a revised version
            if response_data.get("revised_job_title"):
                update_data["job_title"] = response_data.get("revised_job_title")
            
            # Update job description if AI provided an improved version
            if response_data.get("job_description_recommended"):
                update_data["job_description"] = response_data.get("job_description_recommended")
            
            # Update approval status
            if response_data.get("job_approval_status"):
                update_data["job_approval_status"] = response_data.get("job_approval_status")
            
            # Only update if we have changes
            if update_data:
                updated_jobreq = update_jobreq(job_id, **update_data)
                print(f"✅ Successfully updated job request {job_id}")
                print(f"📝 Updated fields: {list(update_data.keys())}")
            else:
                print("ℹ️ No updates needed - no changes from AI processing")
                
        except Exception as e:
            print(f"❌ Error updating job request: {e}")
            # Don't raise here - we still want to return the response even if DB update fails

        # return templates.TemplateResponse("create_jobreq.html", context)
        # Return the structured response using your Pydantic model
        return JobReqResponse(
            job_id=response_data.get("job_id", job_id),
            job_experience_level=response_data.get("job_experience_level", ""),
            job_title=response_data.get("job_title", ""),
            revised_job_title=response_data.get("revised_job_title", ""),
            job_description=response_data.get("job_description", ""),
            job_description_analysis=response_data.get("job_description_analysis", ""),
            job_description_recommended=response_data.get("job_description_recommended", ""),
            job_type=response_data.get("job_type", ""),
            job_approval_status=response_data.get("job_approval_status", "")
        ) 

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process agent query: {e}")
