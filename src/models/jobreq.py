from sqlalchemy import Column, String, Text, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class JobReq(Base):
    __tablename__ = "job_reqs"

    job_id = Column(String, primary_key=True, index=True)
    job_type = Column(String, nullable=False)
    employment_type = Column(String, nullable=False)
    job_experience_level = Column(String, nullable=False)
    job_title = Column(String, nullable=False)
    job_location = Column(String, nullable=False)
    salary_min = Column(Integer, nullable=False)
    salary_max = Column(Integer, nullable=False)
    revised_job_title = Column(String)
    job_description = Column(Text, nullable=False)
    job_description_analysis = Column(Text)
    job_description_recommended = Column(Text)
    required_skills = Column(Text)
    preferred_skills = Column(Text)
    engagement_questions = Column(Text)
    job_approval_status = Column(String, nullable=False)
    job_approval_status_tracker_id = Column(String)
    job_approval_status_notes_by_approver = Column(Text)
