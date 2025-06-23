from fastapi import APIRouter, Request, Form, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from util import SessionLocal
from services.jobreq_service import create_jobreq, process_jobreq_after_creation
from models.jobreq import JobReq
import markupsafe

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def nl2br_filter(value):
    """Convert newlines to HTML line breaks"""
    if value is None:
        return ""
    return markupsafe.Markup(str(value).replace('\n', '<br>'))

router = APIRouter()
templates = Jinja2Templates(directory="templates")
templates.env.filters['nl2br'] = nl2br_filter

@router.get("/create-jobreq", response_class=HTMLResponse)
async def create_jobreq_page(request: Request):
    return templates.TemplateResponse("jobreq/create_jobreq.html", {"request": request})

@router.get("/view-jobreq-all", response_class=HTMLResponse)
async def view_jobreq_all_page(request: Request):
    # Get all jobreqs from the database
    db = SessionLocal()
    jobreqs = db.query(JobReq).all()
    db.close()
    return templates.TemplateResponse(
        "jobreq/view_jobreq_all.html", 
        {
            "request": request,
            "jobreqs": jobreqs
        }
    )

@router.get("/jobreq/{job_id}", response_class=HTMLResponse)
async def view_jobreq_details_page(request: Request, job_id: str):
    print("job_id: " + job_id)
    db = SessionLocal()
    jobreq = db.query(JobReq).filter(JobReq.job_id == job_id).first()
    db.close()
    return templates.TemplateResponse(
        "jobreq/view_jobreq_details.html",
        {
            "request": request,
            "jobreq": jobreq
        }
    )

@router.post("/create-jobreq", response_class=HTMLResponse)
async def submit_jobreq_form(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    job_type: str = Form(...),
    employment_type: str = Form(...),
    job_experience_level: str = Form(...),
    job_title: str = Form(...),
    job_description: str = Form(...),
    required_skills: str = Form(""),
    preferred_skills: str = Form(""),
    engagement_questions: str = Form(""),
    job_location: str = Form(""),
    salary_min: int = Form(0),
    salary_max: int = Form(0),
):
    # Here you can process/store the data as needed
    jobreq_data = {
        "job_type": job_type,
        "employment_type": employment_type,
        "job_experience_level": job_experience_level,
        "job_title": job_title,
        "job_description": job_description,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "engagement_questions": engagement_questions,
        "job_location": job_location,
        "salary_min": salary_min,
        "salary_max": salary_max,
    }
    
    # Step 1: Write to database
    jobreq = create_jobreq(jobreq_data)
    
    # Step 2: Add async task to background tasks with session service
    # Access session_service through request.app.state
    session_service = request.app.state.session_service
    background_tasks.add_task(process_jobreq_after_creation, str(jobreq.job_id), job_title, session_service)
    
    # Step 3: Return response immediately (async task runs in background)
    return templates.TemplateResponse(
        "jobreq/create_jobreq.html",
        {
            "request": request,
            "message": "Job Requisition submitted. (" + str(jobreq.job_id) + ")",
            "job_id": str(jobreq.job_id),
        }
    )
