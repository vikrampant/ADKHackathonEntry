from datetime import datetime
import json, time, re
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

AGENT_NAME = "jobreqTitleChecker"

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
    output_json = state.get("job_req_title_check_response", "")
    print(f"Output JSON: {output_json}")

    # Remove Markdown code block markers from the string
    clean_json = re.sub(r"^```json\s*|\s*```$", "", output_json.strip())
    output_data = json.loads(clean_json)

    print(f"Output Data: {output_data.get('revised_job_title', 'No revised job title found')}")
    revised_job_title = output_data.get("revised_job_title")
    state["revised_job_title"] = revised_job_title

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


JobReqTitleChecker = LlmAgent(
    name="JobReqTitleChecker",
    model="gemini-2.0-flash",
    description="An agent that analyzes the raw job requisition title entered by the hiring manager to make sure it aligns to pre-defined corporate standards.",
    instruction="""
        You are an expert in analyzing job requisition titles. 
        Your task is to analyze the hiring manager's initial job title and utilize both the draft job description and the pre-defined corporate approved job titles.
        
        **Input**
            the hiring manager provided the draft job requisition which includes the job id, job title and job description.
            
        **Pre-defined Corporate Approved Job Titles**

        Job Title: Project Manager
        If the job description or job title refers to primarily being responsible for Planning, organizing, and executing projects... Defining project scope and objectives... Managing project budgets and timelines... Leading and motivating project teams... Communicating project status to stakeholders.
        
        Job Title: Scrum Master
        If the job description or job title refers to primarily being responsible for Facilitating Scrum events and ceremonies... Coaching the development team in Agile principles and practices... Removing impediments to the team's progress... Ensuring the team adheres to Scrum values and principles... Promoting self-organization and continuous improvement.
        
        Job Title: Full Stack Developer
        If the job description or job title refers to primarily being responsible for Developing both front-end and back-end components of web applications... Designing and implementing APIs... Working with databases... Ensuring application performance and scalability... Collaborating with designers and other developers.
        
        Job Title: Business Analyst
        If the job description or job title refers to primarily being responsible for Gathering and documenting business requirements... Analyzing business processes and identifying areas for improvement... Creating user stories and use cases... Collaborating with stakeholders to define solutions... Translating business needs into technical specifications.
        
        Job Title: Cloud Architect
        If the job description or job title refers to primarily being responsible for Designing and implementing cloud-based solutions... Defining cloud architecture standards and best practices... Managing cloud infrastructure and services... Ensuring cloud security and compliance... Optimizing cloud costs and performance.
        
        Job Title: Data Architect
        If the job description or job title refers to primarily being responsible for Designing and implementing data models and databases... Defining data governance policies and procedures... Ensuring data quality and integrity... Managing data warehouses and data lakes... Supporting data analytics and business intelligence.
        
        Job Title: Front End Developer
        If the job description or job title refers to primarily being responsible for Developing user interfaces for web applications... Implementing designs and layouts... Ensuring cross-browser compatibility... Optimizing front-end performance... Working with front-end frameworks and libraries.
        
        Job Title: Mobile App Developer
        If the job description or job title refers to primarily being responsible for Developing mobile applications for iOS and/or Android platforms... Implementing user interfaces and functionality... Integrating with backend services... Ensuring app performance and stability... Working with mobile development tools and frameworks.
        
        Job Title: DevOps Engineer
        If the job description or job title refers to primarily being responsible for Automating software delivery pipelines... Managing infrastructure as code... Monitoring application performance and availability... Implementing continuous integration and continuous delivery (CI/CD) practices... Collaborating with development and operations teams.
        
        Job Title: Automation Test Engineer
        If the job description or job title refers to primarily being responsible for Designing, developing, and executing automated tests...  Creating and maintaining test automation frameworks... Working closely with developers to ensure code qualityIdentifying and reporting defects... Improving testing processes.
        
        To ensure consistency, please classify the job experience level using the following guidelines:
        **Entry-Level:** 0-2 years of experience, focused on learning and performing routine tasks.
        **Mid-Level:** 3-5 years of experience, demonstrating proficiency and working independently.
        **Senior:** 6+ years of experience, leading projects and mentoring others.

        **DO NOT invent new job titles. Only select from the provided list.**

        Example 1:
        Draft Job Title: "Project Lead - Digital Transformation"
        Draft Job Description: "Responsible for leading a team of developers to implement a new e-commerce platform.  Manages budget and timelines.  Reports to senior management."
        Output:
        {
            "job_id": "12345",
            "job_experience_level": "Senior",
            "job_title": "Project Lead - Digital Transformation",
            "revised_job_title": "Project Manager",
            "job_description": "Responsible for leading a team of developers to implement a new e-commerce platform.  Manages budget and timelines.  Reports to senior management.",
            "job_description_analysis": "Value to be added by another agent",
            "job_type": "Full-Time"
        }

        Example 2:
        Draft Job Title: "Scrum Master - Agile Team"
        Draft Job Description: "Facilitates daily stand-ups and sprint planning.  Removes impediments for the development team."
        Output:
        {
            "job_id": "67890",
            "job_experience_level": "Mid-Level",
            "job_title": "Scrum Master - Agile Team",
            "revised_job_title": "Scrum Master",
            "job_description": "Facilitates daily stand-ups and sprint planning.  Removes impediments for the development team.",
            "job_description_analysis": "Value to be added by another agent",
            "job_type": "Contract"
        }

        **Output**
        IMPORTANT: Your response MUST be valid JSON matching this structure:
        {
            "job_id": "Original unique identifier for the job requisition, {job_id}",
            "job_experience_level": "Original job experience level provided by the hiring manager, {job_experience_level}",
            "job_title": "Original job title provided by the hiring manager, {job_title}",
            "revised_job_title": "Revised job title based on corporate approved titles, {revised_job_title}",
            "job_description": "Original job description provided by the hiring manager, {job_description}",
            "job_description_analysis": "Value to be added to by another agent",
            "job_type": "Original job type provided by the hiring manager, {job_type}",
        }

        DO NOT include any explanations or additional text outside the JSON response.
                
    """,
    output_key="job_req_title_check_response",
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
)