from datetime import datetime
import json, time, re
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from services.jobreq_service import get_jobreq

AGENT_NAME = "candidateLocationReview"

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

    # Get the job from database
    job_id = state.get("job_id", "unknown")
    job = get_jobreq(job_id)
    if job:
        print(f"Job Location: {job.job_location}")
        state["job_location"] = job.job_location
    else:
        print(f"Job with ID {job_id} not found")
        state["job_location"] = "unknown"

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

    # Get the session state
    state = callback_context.state

    # Access the agent's output (JSON string)
    output_json = state.get("candidate_location_review_response", "")
    print(f"Output JSON: {output_json}")

    # Remove Markdown code block markers from the string
    clean_json = re.sub(r"^```json\s*|\s*```$", "", output_json.strip())
    output_data = json.loads(clean_json)

    # Store the output data in the state
    state["candidate_location_review_is_located_in_desired_location"] = output_data.get("is_located_in_desired_location", "unknown")
    state["candidate_location_review_reasoning"] = output_data.get("reasoning", "unknown")
    print(f"Candidate Location Review is_located_in_desired_location: {state['candidate_location_review_is_located_in_desired_location']}")
    print(f"Candidate Location Review reasoning: {state['candidate_location_review_reasoning']}")

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


CandidateLocationReview = LlmAgent(
    name="CandidateLocationReview",
    model="gemini-2.0-flash",
    description="An agent that analyzes the resume content provided by the candidate to determine if the candidate is located in the desired location.",
    instruction="""
        Your task is to analyze the resume content provided by the candidate to determine if the candidate is located in the desired location.

        **Input**
            the candidate provided the resume content.
            the job location is {job_location}

        **Output**
        IMPORTANT: Your response MUST be valid JSON matching this structure:
        {
            "is_located_in_desired_location": "boolean, true if the candidate is located in the desired location, false otherwise.  If no location can be determind, return unknown",
            "reasoning": "string, the reasoning for the answer",
        }

        DO NOT include any explanations or additional text outside the JSON response.
                
    """,
    output_key="candidate_location_review_response",
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
)