from datetime import datetime
import json, time, re
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

AGENT_NAME = "jobreqDescriptionChecker"

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
    output_json = state.get("job_req_description_check_response", "")
    print(f"Output JSON: {output_json}")

    # Remove Markdown code block markers from the string
    clean_json = re.sub(r"^```json\s*|\s*```$", "", output_json.strip())
    output_data = json.loads(clean_json)

    print(f"Output Data: {output_data.get('job_description_analysis', 'No analysis found')}")
    state["job_description_analysis"] = output_data.get("job_description_analysis")
    print(f"Output Data: {output_data.get('job_description_recommended', 'No recommendation found')}")
    state["job_description_recommended"] = output_data.get("job_description_recommended", "")

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

JobReqDescriptionChecker = LlmAgent(
    name="JobReqDescriptionChecker",
    model="gemini-2.0-flash",
    description="An agent that analyzes the draft job description.",
    instruction="""
        You are an expert in analyzing job descriptions. 
        Your task is to analyze the hiring manager's initial job description and the pre-defined corporate approved style.

        **Corporate Approved Style:** Emphasizes clear, concise language, action verbs, and a focus on measurable outcomes. Avoid jargon and overly technical terms. Use the STAR method (Situation, Task, Action, Result) to describe responsibilities.  Examples of corporate approved descriptions can be found at [link to internal style guide].
        **Alignment with Corporate Standards:**  Ensures the description accurately reflects the role's responsibilities and reporting structure, and adheres to our company's branding guidelines.
        **Task**
            Provide a detailed analysis of the job description, including:
            - Clarity and completeness of the job responsibilities
            - Alignment with corporate standards
            - Suggestions for improvement focusing on clarity, completeness, and adherence to the STAR method.
            The tone of your analysis should be constructive and professional.

        **Input**
            the hiring manager provided the draft job requisition which includes job description.
                        
        **Output**
        IMPORTANT: Your response MUST be valid JSON matching this structure:
        {
            "job_id": "Original unique identifier for the job requisition",
            "job_experience_level": "Original job experience level provided by the hiring manager",
            "job_title": "Original job title provided by the hiring manager",
            "revised_job_title": "Revised job title based on corporate standards",
            "job_description": "Original job description provided by the hiring manager",
            "job_description_analysis": "The detailed analysis of the job description",
            "job_description_recommended": "Provide a new job description based on the recommendations if any.  Only provide the suggestion, nothing else.",
            "job_type": "Original job type provided by the hiring manager",
        }

        DO NOT include any explanations or additional text outside the JSON response.        
        """,
    # input_schema=JobReqResponse,
    # output_schema=JobReqResponse,
    output_key="job_req_description_check_response",
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
)