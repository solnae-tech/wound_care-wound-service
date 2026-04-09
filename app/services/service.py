from __future__ import annotations

from datetime import date, datetime, time, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session, selectinload

from core.config import settings
from db import models
from services.ai_job_service import submit_wound_to_ai_service
from schema.schema import (
    AIJobCreateResponse,
    DashboardAlert,
    DashboardCaseCard,
    DashboardResponse,
    DoctorCard,
    JobStatusResponse,
    DoctorsResponse,
    ProgressResponse,
    TimelineItem,
    WoundAnalysisResponse,
    WoundCreate,
    WoundEntryJobResponse,
    WoundEntryOut,
    WoundListItem,
    WoundOut,
)


DEFAULT_USER_EMAIL = "demo@solnea.local"
DEFAULT_USER_PHONE = "9999999999"
WOUND_TYPE_MAP = {
    "surgical": "surgical",
    "surgery": "surgical",
    "burn": "burn",
    "accident": "accident",
    "injury": "accident",
    "other": "other",
}
STATUS_SCORE_MAP = {
    "open": 48,
    "infected": 40,
    "healing": 76,
    "closed": 100,
}
JOB_STATUS_QUEUED = "queued"
_ai_job_queue: list[dict[str, object]] = []
_ai_jobs: dict[str, dict[str, object]] = {}


def _score_label(score: int) -> str:
    if score >= 85:
        return "Strong Healing"
    if score >= 70:
        return "Moderate Healing"
    if score >= 50:
        return "Needs Attention"
    return "Critical Review"


def _infection_risk(score: int, pain_level: int) -> str:
    if score < 55 or pain_level >= 8:
        return "High"
    if score < 75 or pain_level >= 5:
        return "Moderate"
    return "Low"


def _healing_rate(score: int) -> str:
    if score >= 80:
        return "Improving"
    if score >= 65:
        return "Steady"
    return "Slow"


def _color_analysis(score: int) -> str:
    if score < 70:
        return "Redness present"
    if score < 85:
        return "Mild redness"
    return "Healthy tone"


def _summary_text(wound_name: str, score: int, pain_level: int, notes: str | None) -> str:
    base = (
        f"{wound_name} is currently {_score_label(score).lower()}. "
        f"Pain level is {pain_level}/10 and the wound appears {_color_analysis(score).lower()}."
    )
    if notes:
        return f"{base} Patient notes: {notes}"
    return base


def _alert_message(score: int, pain_level: int) -> str | None:
    if score < 70 or pain_level >= 6:
        return "Signs of possible infection detected. Consider consulting a doctor."
    return None


def _save_upload(file: UploadFile | None) -> str | None:
    if not file or not file.filename:
        return None

    upload_dir = Path(getattr(settings, "upload_dir", "uploads"))
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename).suffix or ".jpg"
    filename = f"{uuid4().hex}{suffix}"
    destination = upload_dir / filename

    with destination.open("wb") as buffer:
        buffer.write(file.file.read())

    return str(destination).replace("\\", "/")


def _recorded_at_as_datetime(recorded_at: date) -> datetime:
    return datetime.combine(recorded_at, time.min)


def _normalize_wound_type(value: str | None) -> str:
    if not value:
        return "other"
    normalized = value.strip().lower()
    return WOUND_TYPE_MAP.get(normalized, "other")


def _get_or_create_default_user(db: Session) -> models.Users:
    user = db.query(models.Users).filter(models.Users.email == DEFAULT_USER_EMAIL).first()
    if user:
        return user

    user = models.Users(
        full_name="Demo User",
        email=DEFAULT_USER_EMAIL,
        phone_number=DEFAULT_USER_PHONE,
        password_hash="demo-password",
        is_verified=True,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def get_user_or_404(db: Session, user_id: int) -> models.Users:
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _get_sorted_history(wound: models.Wounds) -> list[models.WoundHistory]:
    return sorted(
        wound.wound_history,
        key=lambda entry: (entry.recorded_at, entry.created_at or datetime.min),
        reverse=True,
    )


def _display_wound_name(wound: models.Wounds) -> str:
    location = wound.location.strip() if wound.location else "Unknown Location"
    return f"{location} {wound.wound_type.title()}".strip()


def _build_entry_view(
    wound: models.Wounds,
    entry: models.WoundHistory,
    previous_entry: models.WoundHistory | None = None,
) -> WoundEntryOut:
    pain_level = entry.pain_level or 0
    base_score = STATUS_SCORE_MAP.get(entry.status, 45)
    healing_score = max(35, min(100, base_score + max(0, 5 - pain_level) * 3))
    description = entry.description
    image_path = entry.wound_image_url
    infection_risk = _infection_risk(healing_score, pain_level)
    color_analysis = _color_analysis(healing_score)
    healing_rate = _healing_rate(healing_score)
    alert_message = _alert_message(healing_score, pain_level)
    wound_size = round(max(0.0, 7.2 - (healing_score / 20)), 1)
    image_source = "camera" if image_path else "manual"

    if previous_entry:
        previous_score = STATUS_SCORE_MAP.get(previous_entry.status, 45) + max(0, 5 - (previous_entry.pain_level or 0)) * 3
        if healing_score > previous_score:
            healing_rate = "Improving"
        elif healing_score < previous_score:
            healing_rate = "Slow"

    return WoundEntryOut(
        id=entry.id,
        wound_id=wound.id,
        job_id=entry.job_id,
        image_path=image_path,
        image_source=image_source,
        pain_level=pain_level,
        notes=description,
        dressing_changed=False,
        healing_score=healing_score,
        healing_label=_score_label(healing_score),
        wound_size_cm2=wound_size,
        infection_risk=infection_risk,
        color_analysis=color_analysis,
        healing_rate=healing_rate,
        ai_summary=_summary_text(_display_wound_name(wound), healing_score, pain_level, description),
        alert_message=alert_message,
        captured_at=_recorded_at_as_datetime(entry.recorded_at),
    )

def _serialize_history_entry(entry: models.WoundHistory | None) -> dict[str, object] | None:
    if not entry:
        return None
    return {
        "id": entry.id,
        "recorded_at": entry.recorded_at,
        "status": entry.status,
        "job_id": entry.job_id,
        "wound_image_url": entry.wound_image_url,
        "pain_level": entry.pain_level,
        "description": entry.description,
    }


def _enqueue_ai_job(job: dict[str, object]) -> None:
    _ai_job_queue.append(job)


def _build_wound_out(wound: models.Wounds) -> WoundOut:
    history = _get_sorted_history(wound)
    latest_entry = None
    if history:
        next_entry = history[1] if len(history) > 1 else None
        latest_entry = _build_entry_view(wound, history[0], next_entry)

    return WoundOut(
        id=wound.id,
        name=_display_wound_name(wound),
        cause=wound.wound_type,
        body_location=wound.location or "",
        body_side="front",
        status=wound.status,
        created_at=wound.created_at or _recorded_at_as_datetime(wound.first_noted_at),
        updated_at=wound.updated_at or _recorded_at_as_datetime(wound.first_noted_at),
        latest_entry=latest_entry,
    )


def get_wound_or_404(db: Session, user_id: int, wound_id: int) -> models.Wounds:
    wound = (
        db.query(models.Wounds)
        .options(selectinload(models.Wounds.wound_history))
        .filter(models.Wounds.id == wound_id, models.Wounds.user_id == user_id)
        .first()
    )
    if not wound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wound not found")
    return wound


def get_wound(db: Session, user_id: int, wound_id: int) -> WoundOut:
    wound = get_wound_or_404(db, user_id, wound_id)
    return _build_wound_out(wound)


def list_wounds(user_id: int, db: Session) -> list[WoundOut]:
    get_user_or_404(db, user_id)
    wounds = (
        db.query(models.Wounds)
        .options(selectinload(models.Wounds.wound_history))
        .filter(models.Wounds.user_id == user_id)
        .order_by(models.Wounds.updated_at.desc())
        .all()
    )
    return [_build_wound_out(wound) for wound in wounds]


def add_wound_entry(
    db: Session,
    user_id: int,
    wound_id: int,
    pain_level: int,
    dressing_changed: bool,
    notes: str | None,
    file: UploadFile | None,
) -> AIJobCreateResponse:
    get_wound_or_404(db, user_id, wound_id)
    description = notes
    if dressing_changed:
        description = f"{notes} Dressing changed.".strip() if notes else "Dressing changed."
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wound image is required")

    job_response = submit_wound_to_ai_service(
        user_id=str(user_id),
        pain_level=pain_level,
        description=description or "",
        file=file,
    )
    return AIJobCreateResponse(job_id=job_response["job_id"])


def get_job_status(job_id: str) -> JobStatusResponse:
    job = _ai_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        wound_id=job.get("wound_id"),
        entry_id=job.get("entry_id"),
    )


def get_latest_analysis(db: Session, user_id: int, wound_id: int) -> WoundAnalysisResponse:
    wound = get_wound_or_404(db, user_id, wound_id)
    history = _get_sorted_history(wound)
    if not history:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No analysis available yet")

    latest = _build_entry_view(wound, history[0], history[1] if len(history) > 1 else None)
    return WoundAnalysisResponse(
        wound_id=wound.id,
        wound_name=_display_wound_name(wound),
        captured_at=latest.captured_at,
        healing_score=latest.healing_score,
        healing_label=latest.healing_label,
        metrics=[
            {"title": "Wound Size", "value": f"{latest.wound_size_cm2} cm2", "subtitle": "Estimated from healing status"},
            {"title": "Infection Risk", "value": latest.infection_risk, "subtitle": "Derived from pain and status"},
            {"title": "Color Analysis", "value": latest.color_analysis, "subtitle": None},
            {"title": "Healing Rate", "value": latest.healing_rate, "subtitle": "Trend over recent entries"},
        ],
        ai_summary=latest.ai_summary,
        alert_message=latest.alert_message,
    )


def get_progress(db: Session, user_id: int, wound_id: int, selected_range: str) -> ProgressResponse:
    wound = get_wound_or_404(db, user_id, wound_id)
    history = _get_sorted_history(wound)
    days = {"7d": 7, "14d": 14, "30d": 30}.get(selected_range, 7)
    cutoff = date.today() - timedelta(days=days)
    filtered_history = [entry for entry in history if entry.recorded_at >= cutoff] or history[:days]

    entry_views = [
        _build_entry_view(
            wound,
            entry,
            filtered_history[index + 1] if index + 1 < len(filtered_history) else None,
        )
        for index, entry in enumerate(filtered_history)
    ]
    ordered_entries = list(reversed(entry_views))

    chart_points = [
        {"label": f"D{index + 1:02d}", "score": entry.healing_score}
        for index, entry in enumerate(ordered_entries)
    ]
    timeline = [
        TimelineItem(
            entry_id=entry.id,
            day_label="Today" if index == 0 else f"Day {len(entry_views) - index}",
            score=entry.healing_score,
            summary=entry.ai_summary,
            image_path=entry.image_path,
            captured_at=entry.captured_at,
        )
        for index, entry in enumerate(entry_views)
    ]
    return ProgressResponse(
        wound_id=wound.id,
        wound_name=_display_wound_name(wound),
        selected_range=selected_range,
        chart_points=chart_points,
        timeline=timeline,
    )


def get_doctors(user_id: int, db: Session) -> DoctorsResponse:
    get_user_or_404(db, user_id)
    return DoctorsResponse(
        doctors=[
            DoctorCard(id=1, name="Dr. Priya Nair", specialty="Dermatology", hospital="City Care Clinic", availability="Today 4:30 PM"),
            DoctorCard(id=2, name="Dr. Arjun Rao", specialty="Wound Management", hospital="Greenline Hospital", availability="Tomorrow 10:00 AM"),
            DoctorCard(id=3, name="Dr. Meera Joseph", specialty="General Surgery", hospital="Apollo Health Center", availability="Tomorrow 1:15 PM"),
        ]
    )


def humanize_delta(delta: timedelta) -> str:
    hours = int(delta.total_seconds() // 3600)
    if hours < 1:
        minutes = max(1, int(delta.total_seconds() // 60))
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    days = delta.days
    return f"{days} day{'s' if days != 1 else ''}"


def seed_demo_data(db: Session) -> None:
    if db.query(models.Wounds).first():
        return

    user = _get_or_create_default_user(db)
    wound_1 = models.Wounds(
        user_id=user.id,
        wound_type="accident",
        status="healing",
        first_noted_at=date.today() - timedelta(days=7),
        location="Left Knee",
        created_at=datetime.utcnow() - timedelta(days=7),
        updated_at=datetime.utcnow() - timedelta(hours=2),
    )
    wound_2 = models.Wounds(
        user_id=user.id,
        wound_type="burn",
        status="closed",
        first_noted_at=date.today() - timedelta(days=15),
        location="Right Forearm",
        closed_at=date.today() - timedelta(days=12),
        created_at=datetime.utcnow() - timedelta(days=15),
        updated_at=datetime.utcnow() - timedelta(days=12),
    )
    db.add_all([wound_1, wound_2])
    db.flush()

    entries = [
        models.WoundHistory(
            wound_id=wound_1.id,
            recorded_at=date.today() - timedelta(days=3),
            status="infected",
            wound_image_url="images/sc1.jpg",
            pain_level=6,
            description="Redness slightly increased from yesterday. Dressing changed.",
        ),
        models.WoundHistory(
            wound_id=wound_1.id,
            recorded_at=date.today() - timedelta(days=1),
            status="healing",
            wound_image_url="images/WhatsApp Image 2026-04-08 at 11.55.08 AM.jpeg",
            pain_level=5,
            description="Swelling reduced compared to Day 3. Dressing changed.",
        ),
        models.WoundHistory(
            wound_id=wound_1.id,
            recorded_at=date.today(),
            status="healing",
            wound_image_url="images/WhatsApp Image 2026-04-08 at 11.55.08 AM (1).jpeg",
            pain_level=4,
            description="Minimal redness at the distal edge. Dressing changed.",
        ),
        models.WoundHistory(
            wound_id=wound_2.id,
            recorded_at=date.today() - timedelta(days=12),
            status="closed",
            wound_image_url="images/WhatsApp Image 2026-04-08 at 11.55.07 AM.jpeg",
            pain_level=0,
            description="Closed and dry.",
        ),
    ]
    db.add_all(entries)
    db.commit()
