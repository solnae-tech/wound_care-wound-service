from __future__ import annotations

import base64
import json
import os
from urllib import error, request
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status


def submit_wound_to_ai_service(
    user_id: str,
    pain_level: int,
    description: str,
    file: UploadFile,
    ) -> dict[str, str]:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wound image is required")

    payload = {
        "user_id": user_id,
        "job_id": uuid4().hex,
        "wound_img": base64.b64encode(file.file.read()).decode("utf-8"),
        "pain_level": pain_level,
        "description": description,
    }

    ai_service_url = os.getenv("AI_SERVICE_URL", "").rstrip("/")
    if not ai_service_url:
        return {"job_id": payload["job_id"]}

    req = request.Request(
        url=f"{ai_service_url}/jobs",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=15) as response:
            response_body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        raise HTTPException(status_code=exc.code, detail="AI service request failed") from exc
    except error.URLError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is unreachable",
        ) from exc

    if not response_body:
        return {"job_id": payload["job_id"]}

    try:
        response_json = json.loads(response_body)
    except json.JSONDecodeError:
        return {"job_id": payload["job_id"]}

    if isinstance(response_json, dict) and isinstance(response_json.get("job_id"), str):
        return {"job_id": response_json["job_id"]}

    return {"job_id": payload["job_id"]}
