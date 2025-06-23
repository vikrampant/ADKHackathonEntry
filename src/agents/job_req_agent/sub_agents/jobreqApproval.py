import asyncio
import random
from typing import Any
from google.adk.agents import Agent
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.tools import LongRunningFunctionTool
from google.adk.sessions import DatabaseSessionService
from google.genai import types
from datetime import datetime
import json, time, re
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

# 1. Define the long running function
def ask_for_approval() -> dict[str, str]:
    job_approval_status_tracker_id = random.randint(1000, 9999)
    print(f"Job approval status tracker ID: {job_approval_status_tracker_id}")
    return {
        "job_approval_status": 'pending-approval',
        "job_approval_status_tracker_id": str(job_approval_status_tracker_id),
    }

def approve() -> dict[str, str]:
    return {
        "job_approval_status": 'approved',
        "job_approval_status_tracker_id": 'n/a',
        "job_approval_status_notes_by_approver": "approved",
    }

# 2. Wrap the function with LongRunningFunctionTool
long_running_tool = LongRunningFunctionTool(func=ask_for_approval)

AGENT_NAME = "jobreqApproval"

def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Simple callback that logs when the agent starts processing a request.

    Args:
        callback_context: Contains state and context information

    Returns:
        None to continue with normal agent processing
    """
    # Get the session state
    state = callback_context.state

    # Record timestamp
    timestamp = datetime.now()

    # Set agent name if not present
    if "agent_name" not in state:
        state["agent_name"] = AGENT_NAME

    # Initialize request counter
    if "request_counter" not in state:
        state["request_counter"] = 1
    else:
        state["request_counter"] += 1

    # Store start time for duration calculation in after_agent_callback
    # state["request_start_time"] = timestamp
    state["request_start_time"] = timestamp.isoformat()

    # Log the request
    print("=== AGENT EXECUTION STARTED ===")
    print(f"Request #: {state['request_counter']}")
    print(f"Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    # Print to console
    print(f"\n[BEFORE CALLBACK] Agent processing request #{state['request_counter']}")

    return None

def after_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Simple callback that logs when the agent finishes processing a request.

    Args:
        callback_context: Contains state and context information

    Returns:
        None to continue with normal agent processing
    """

    # Sleep for 2 seconds to ensure agent output in state
    # time.sleep(2)

    # Get the session state
    state = callback_context.state

    # Access the agent's output (JSON string)
    output_json = state.get("job_req_approval_response", "")
    print(f"Output JSON: {output_json}")

    # Remove Markdown code block markers from the string
    clean_json = re.sub(r"^```json\s*|\s*```$", "", output_json.strip())
    output_data = json.loads(clean_json)

    print(f"Output Data: {output_data.get('job_approval_status', 'No status found')}")
    state["job_approval_status"] = output_data.get("job_approval_status")

    print(f"Output Data: {output_data.get('job_approval_status_tracker_id', 'No status found')}")
    state["job_approval_status_tracker_id"] = output_data.get("job_approval_status_tracker_id")

    print(f"Output Data: {output_data.get('job_approval_status_notes_by_approver', 'No notes found')}")
    state["job_approval_status_notes_by_approver"] = output_data.get("job_approval_status_notes_by_approver")

    # Calculate request duration if start time is available
    timestamp = datetime.now()
    duration = None
    if "request_start_time" in state:
        duration = (timestamp - datetime.fromisoformat(state["request_start_time"])).total_seconds()

    # Log the completion
    print("=== AGENT EXECUTION COMPLETED ===")
    print(f"Request #: {state.get('request_counter', 'Unknown')}")
    if duration is not None:
        print(f"Duration: {duration:.2f} seconds")

    # Print to console
    print(
        f"[AFTER CALLBACK] Agent completed request #{state.get('request_counter', 'Unknown')}"
    )
    if duration is not None:
        print(f"[AFTER CALLBACK] Processing took {duration:.2f} seconds")

    return None

# 3. Use the tool in an Agent
JobReqApproval = Agent(
    # Use a model compatible with function calling
    model="gemini-2.0-flash",
    name='jobreq_approval_agent',
    instruction="""
        You are a job requisition approval agent. Your task is to handle the job requisition approval process. 
        
        If the job_experience_level is experience_level_entry_level (representing 0-2 years of experience), 
        you will automatically approve and set the job_approval_status to approved.
        
        If the employee's job_experience_level is anything else, you will ask for approval by calling the ask_for_approval tool.  
        And the results of the response, including the status tracker id, will be updated in the output.
        
        **Output**
        IMPORTANT: Your response MUST be valid JSON matching this structure:
        {
            "job_id": "Original unique identifier for the job requisition, {job_id}",
            "job_experience_level": "Original job experience level provided by the hiring manager, {job_experience_level}",
            "job_title": "Original job title provided by the hiring manager, {job_title}",
            "revised_job_title": "Revised job title based on corporate approved titles, {revised_job_title}",
            "job_description": "Original job description provided by the hiring manager, {job_description}",
            "job_description_analysis": "The detailed analysis of the job description",
            "job_description_recommended": "Provide a new job description based on the recommendations if any.  Only provide the suggestion, nothing else.",            
            "job_type": "Original job type provided by the hiring manager, {job_type}",
            "job_approval_status": "The result of the job requisition approval process, either 'approved' or 'pending'. If the job_experience_level is entry level, it will be set to 'approved'. If the job_experience_level is mid level, senior or SME, it will be set to 'pending' and you will ask for approval from the manager.",
            "job_approval_status_tracker_id": "A unique identifier for tracking the job approval status, if needed.",
            "job_approval_status_notes_by_approver": "Any notes provided by the approver. If job_experience_level is entry level, add note that this was auto-approved. Otherwise set to 'n/a'. Notes should be brief and indicate the reason for approval or rejection."
        }
        DO NOT include any explanations or additional text outside the JSON response.    
        """,
    output_key="job_req_approval_response",
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    tools=[approve, long_running_tool]
)

# # Agent Interaction
# async def call_agent(query, session, runner, session_id, user_id):
#
#     def get_long_running_function_call(event: Event) -> types.FunctionCall:
#         # Get the long running function call from the event
#         if not event.long_running_tool_ids or not event.content or not event.content.parts:
#             return
#         for part in event.content.parts:
#             if (
#                 part
#                 and part.function_call
#                 and event.long_running_tool_ids
#                 and part.function_call.id in event.long_running_tool_ids
#             ):
#                 return part.function_call
#
#     def get_function_response(event: Event, function_call_id: str) -> types.FunctionResponse:
#         # Get the function response for the fuction call with specified id.
#         if not event.content or not event.content.parts:
#             return
#         for part in event.content.parts:
#             if (
#                 part
#                 and part.function_response
#                 and part.function_response.id == function_call_id
#             ):
#                 return part.function_response
#
#     content = types.Content(role='user', parts=[types.Part(text=query)])
#     events = runner.run_async(user_id=user_id, session_id=session_id, new_message=content)
#
#     print("\nRunning agent...")
#     events_async = runner.run_async(
#         session_id=session.id, user_id=user_id, new_message=content
#     )
#
#
#     long_running_function_call, long_running_function_response, ticket_id = None, None, None
#     async for event in events_async:
#         # Use helper to check for the specific auth request event
#         if not long_running_function_call:
#             long_running_function_call = get_long_running_function_call(event)
#         else:
#             long_running_function_response = get_function_response(event, long_running_function_call.id)
#             if long_running_function_response:
#                 ticket_id = long_running_function_response.response['job-id']
#         if event.content and event.content.parts:
#             if text := ''.join(part.text or '' for part in event.content.parts):
#                 print(f'[{event.author}]: {text}')
#
#
#     if long_running_function_response:
#         # query the status of the correpsonding ticket via job-id
#         # send back an intermediate / final response
#         updated_response = long_running_function_response.model_copy(deep=True)
#         updated_response.response = {'status': 'approved'}
#         async for event in runner.run_async(
#           session_id=session.id, user_id=user_id, new_message=types.Content(parts=[types.Part(function_response = updated_response)], role='user')
#         ):
#             if event.content and event.content.parts:
#                 if text := ''.join(part.text or '' for part in event.content.parts):
#                     print(f'[{event.author}]: {text}')