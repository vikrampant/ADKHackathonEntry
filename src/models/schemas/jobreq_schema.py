from pydantic import BaseModel
from typing import Optional

class JobReqRequest(BaseModel):
    job_type: str
    employment_type: str
    job_experience_level: str
    job_title: str
    job_description: str
    required_skills: Optional[str] = ""
    preferred_skills: Optional[str] = ""
    engagement_questions: Optional[str] = ""
    job_location: Optional[str] = ""
    salary_min: Optional[int] = 0
    salary_max: Optional[int] = 0
    # company_name: Optional[str] = None
    # location: Optional[str] = None
    # employment_type: Optional[str] = None  # e.g., Full-time, Part-time, Contract
    # salary_range: Optional[str] = None  # e.g., "$50,000 - $70,000"
    # required_skills: Optional[list[str]] = None
    # preferred_skills: Optional[list[str]] = None
    # application_deadline: Optional[str] = None  # e.g., "2023-12-31"

class JobReqResponse(BaseModel):
    job_id: str
    job_experience_level: str
    job_title: str
    revised_job_title: str
    job_description: str
    job_description_analysis: str
    job_description_recommended: str
    job_type: str
    job_approval_status: str
    job_approval_status_tracker_id: Optional[str] = None
    job_approval_status_notes_by_approver: Optional[str] = None
    # company_name: Optional[str] = None
    # location: Optional[str] = None
    # employment_type: Optional[str] = None  # e.g., Full-time, Part-time, Contract
    # salary_range: Optional[str] = None  # e.g., "$50,000 - $70,000"
    # required_skills: Optional[list[str]] = None
    # preferred_skills: Optional[list[str]] = None
    # experience_level: Optional[str] = None  # e.g., Entry-level, Mid-level, Senior-level
    # application_deadline: Optional[str] = None  # e.g., "2023-12-31"

