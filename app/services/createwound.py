from __future__ import annotations

from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from db import models
from schema.schema import WoundCreate


def create_wound_service(db: Session, user_id: int, payload: WoundCreate):
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    wound = models.Wounds(
        user_id=user.id,
        wound_type=payload.cause,
        status="open",
        first_noted_at=date.today(),
        location=payload.body_location
    )
    db.add(wound)
    db.commit()
    db.refresh(wound)
    return("Wound created successfully")