from fastapi import APIRouter, Request, Form, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from util import SessionLocal
from services.candidate_service import process_resume_content_for_job
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

@router.get("/candidates/jobs", response_class=HTMLResponse)
async def candidates_view_all_jobs_page(request: Request):
    db = SessionLocal()
    jobs = db.query(JobReq).all()
    db.close()
    return templates.TemplateResponse(
        "candidate/view_job_all.html", 
        {
            "request": request,
            "jobs": jobs
        }
    )

@router.get("/candidates/jobs/{job_id}", response_class=HTMLResponse)
async def candidates_view_job_details_page(request: Request, job_id: str):
    print("job_id: " + job_id)
    db = SessionLocal()
    job = db.query(JobReq).filter(JobReq.job_id == job_id).first()
    db.close()
    return templates.TemplateResponse(
        "candidate/view_job_details.html",
        {
            "request": request,
            "job": job
        }
    )

@router.get("/candidates/jobs/{job_id}/apply", response_class=HTMLResponse)
async def candidates_apply_to_job_page(request: Request, job_id: str):
    print("job_id: " + job_id)
    return templates.TemplateResponse(
        "candidate/apply_to_job.html",
        {
            "request": request,
            "job_id": job_id
        }
    )

@router.post("/candidates/jobs/{job_id}/apply", response_class=HTMLResponse)
async def candidates_applied_to_job(
    request: Request, 
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    resume_content: str = Form(...)
):
    print("job_id: " + job_id)
    print("resume_content: " + resume_content)

    session_service = request.app.state.session_service
    background_tasks.add_task(process_resume_content_for_job, str(job_id), resume_content, session_service)

    return templates.TemplateResponse(
        "candidate/apply_to_job.html",
        {
            "request": request,
            "job_id": job_id
        }
    )