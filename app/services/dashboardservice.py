from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from db import models
from schema.schema import (
    DashboardAlert,
    DashboardResponse,
    WoundListItem
)

def get_dashboard_service(user_id: int, db: Session) -> DashboardResponse:
    user = db.query(models.Users).filter(models.Users.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    wounds = (
        db.query(models.Wounds)
        .filter(models.Wounds.user_id == user_id)
        .order_by(models.Wounds.updated_at.desc())
        .all()
    )
    alerts: list[DashboardAlert] = []
    wound_cards: list[WoundListItem] = []
    wound_list: list[WoundListItem] = []

    for wound in wounds:
        if wound.status in ['open', 'healing', 'infected']:
            wound_cards.append(
            WoundListItem(
                wound_id=wound.id,
                wound_name=wound.wound_type + " on " + wound.location,
                status=wound.status
                )
            )
        elif wound.status == 'infected':
            alerts.append(
                DashboardAlert(
                    title="Wound Infected",
                    message=f"Wound {wound.wound_type} on {wound.location} is now {wound.status}. Consult your doctor immediately.",
                    severity="high"
                )
            )
        wound_list.append(
        WoundListItem(
            wound_id=wound.id,
            wound_name=wound.wound_type + " on " + wound.location,
            status=wound.status
            )
        )

    return DashboardResponse(alerts=alerts, wound_list=wound_list, wound_cards=wound_cards)