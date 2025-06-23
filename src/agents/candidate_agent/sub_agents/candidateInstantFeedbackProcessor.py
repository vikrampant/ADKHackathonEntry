from datetime import datetime
import json, time, re
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

AGENT_NAME = "candidateInstantFeedbackProcessor"

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

    # Get the session state
    state = callback_context.state

    # Access the agent's output (JSON string)
    output_json = state.get("candidate_instant_feedback_processor_response", "")
    print(f"Output JSON: {output_json}")

    # Remove Markdown code block markers from the string
    clean_json = re.sub(r"^```json\s*|\s*```$", "", output_json.strip())
    output_data = json.loads(clean_json)

    # Store the output data in the state
    state["candidate_response"] = output_data.get("candidate_response", "unknown")
    state["candidate_response_reasoning"] = output_data.get("reasoning", "unknown")
    print(f"Candidate Instant Feedback Processor response: {state['candidate_response']}")
    print(f"Candidate Instant Feedback Processor reasoning: {state['candidate_response_reasoning']}")

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


CandidateInstantFeedbackProcessor = LlmAgent(
    name="CandidateInstantFeedbackProcessor",
    model="gemini-2.0-flash",
    description="An agent that provides instant feedback to the candidate.",
    instruction="""
        Your task is to provide instant feedback to the candidate based on the candidate location review response, candidate experience review response, and candidate skill review response.

        The response should be a no more than three sentences.  Keep response concise and to the point.  
        The response should be tailored for the candidate and be subtle and kind but not hiding the core issue.
        The response should be in the same language as the candidate's resume content.
        The response should state that is not a rejection but a suggestion for improvement.  And that the resume will be reviewed by a human as part of the hiring process.

        **Input**
        the candidate provided the resume content.
        the candidate experience review response is {candidate_experience_review_response}.
        the candidate skill review response is {candidate_skill_review_response}.
        the candidate location review response is {candidate_location_review_response}.

        **Guidelines**
        If the candidate is not located in the desired location, the response should state that the candidate is not located in the desired location.
        If the candidate has no experience in the desired skill, the response should state that the candidate lacks experience, in their resume, in the desired skill.
        If the candidate has no experience in the desired experience, the response should state that the candidate lacks experience in the desired experience.

        **Output**
        IMPORTANT: Your response MUST be valid JSON matching this structure:
        {
            "candidate_response": "string, the response to the candidate.",
            "reasoning": "string, the reasoning for the answer",
        }

        DO NOT include any explanations or additional text outside the JSON response.
                
    """,
    output_key="candidate_instant_feedback_processor_response",
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
)