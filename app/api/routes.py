from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from db.database import get_db
from schema.schema import (
    AIJobCreateResponse,
    DashboardResponse,
    DoctorsResponse,
    JobStatusResponse,
    ProgressResponse,
    WoundAnalysisResponse,
    WoundCreate,
    WoundEntryJobResponse,
    WoundEntryOut,
    WoundOut,
)
from services.dashboardservice import get_dashboard_service
from services.createwound import create_wound_service
from services import service


router = APIRouter()


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(user_id: int, db: Session = Depends(get_db)) -> DashboardResponse:
    return get_dashboard_service(user_id, db)    

@router.post("/wounds", response_model=WoundOut, status_code=201)
def create_wound(user_id: int, payload: WoundCreate, db: Session = Depends(get_db)):
    return create_wound_service(db, user_id, payload)


@router.get("/wounds/{wound_id}", response_model=WoundOut)
def get_wound(wound_id: int, user_id: int, db: Session = Depends(get_db)) -> WoundOut:
    return service.get_wound(db, user_id, wound_id)


@router.post("/wounds/{wound_id}/entries", response_model=AIJobCreateResponse, status_code=201)
def add_wound_entry(
    wound_id: int,
    user_id: int,
    pain_level: int = Form(...),
    dressing_changed: bool = Form(False),
    notes: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db)
 ) -> AIJobCreateResponse:
    return service.add_wound_entry(
        db=db,
        user_id=user_id,
        wound_id=wound_id,
        pain_level=pain_level,
        dressing_changed=dressing_changed,
        notes=notes,
        file=file
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str) -> JobStatusResponse:
    return service.get_job_status(job_id)


@router.get("/wounds/{wound_id}/analysis/latest", response_model=WoundAnalysisResponse)
def get_latest_analysis(wound_id: int, user_id: int, db: Session = Depends(get_db)) -> WoundAnalysisResponse:
    return service.get_latest_analysis(db, user_id, wound_id)


@router.get("/wounds/{wound_id}/progress", response_model=ProgressResponse)
def get_progress(
    wound_id: int,
    user_id: int,
    range_key: str = "7d",
    db: Session = Depends(get_db),
) -> ProgressResponse:
    return service.get_progress(db, user_id, wound_id, range_key)


@router.get("/doctors", response_model=DoctorsResponse)
def get_doctors(user_id: int, db: Session = Depends(get_db)) -> DoctorsResponse:
    return service.get_doctors(user_id, db)
