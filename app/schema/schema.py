from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
    

class WoundCreate(BaseModel):
    cause: str = 'surgical or burn or accident or other'
    body_location: str
    body_side: str = "front"


class WoundEntryCreate(BaseModel):
    pain_level: int = Field(ge=0, le=10)
    notes: str | None = Field(default=None, max_length=500)
    dressing_changed: bool = False
    image_source: str | None = None


class WoundEntryOut(BaseModel):
    id: int
    wound_id: int
    job_id: str | None = None
    image_path: str | None
    image_source: str | None
    pain_level: int
    notes: str | None
    dressing_changed: bool
    healing_score: int
    healing_label: str
    wound_size_cm2: float
    infection_risk: str
    color_analysis: str
    healing_rate: str
    ai_summary: str
    alert_message: str | None
    captured_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WoundOut(BaseModel):
    id: int
    name: str
    cause: str
    body_location: str
    body_side: str
    status: str
    created_at: datetime
    updated_at: datetime
    latest_entry: WoundEntryOut | None = None

    model_config = ConfigDict(from_attributes=True)


class WoundEntryJobResponse(BaseModel):
    job_id: str
    status: str
    wound_id: int
    entry_id: int


class AIJobCreateResponse(BaseModel):
    job_id: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    wound_id: int | None = None
    entry_id: int | None = None


class DashboardAlert(BaseModel):
    title: str
    message: str
    severity: str


class DashboardCaseCard(BaseModel):
    wound_id: int
    wound_name: str
    score: int
    score_label: str
    last_scan_text: str
    healing_tag: str


class WoundListItem(BaseModel):
    wound_id: int
    wound_name: str
    status: str


class DashboardResponse(BaseModel):
    alerts: list[DashboardAlert]
    wound_list: list[WoundListItem]
    wound_cards: list[WoundListItem]


class AnalysisMetricCard(BaseModel):
    title: str
    value: str
    subtitle: str | None = None


class WoundAnalysisResponse(BaseModel):
    wound_id: int
    wound_name: str
    captured_at: datetime
    healing_score: int
    healing_label: str
    metrics: list[AnalysisMetricCard]
    ai_summary: str
    alert_message: str | None


class TimelineItem(BaseModel):
    entry_id: int
    day_label: str
    score: int
    summary: str
    image_path: str | None
    captured_at: datetime


class ProgressResponse(BaseModel):
    wound_id: int
    wound_name: str
    selected_range: str
    chart_points: list[dict[str, str | int]]
    timeline: list[TimelineItem]


class DoctorCard(BaseModel):
    id: int
    name: str
    specialty: str
    hospital: str
    availability: str


class DoctorsResponse(BaseModel):
    doctors: list[DoctorCard]
