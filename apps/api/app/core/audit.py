from uuid import UUID
from typing import Optional, Any, Callable
from functools import wraps
from fastapi import Request, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import AuditLog, Caregiver
from app.core.security import decode_token

def log_audit_event(
    db: Session,
    action: str,
    actor_caregiver_id: Optional[UUID] = None,
    patient_id: Optional[UUID] = None,
    metadata: Optional[dict[str, Any]] = None
) -> AuditLog:
    """
    Creates an audit log entry in audit_logs table.
    Retains record even if patient is later deleted.
    """
    audit_log = AuditLog(
        actor_caregiver_id=actor_caregiver_id,
        patient_id=patient_id,
        action=action,
        action_metadata=metadata
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


def audit_action(action_name: str) -> Callable:
    """
    FastAPI route dependency that automatically logs an audit record
    for sensitive read/write endpoints (recordings, transcripts, photos, consent).
    """
    def dependency(
        request: Request,
        db: Session = Depends(get_db)
    ):
        # Extract actor caregiver ID from JWT authorization header if present
        actor_caregiver_id: Optional[UUID] = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_token(token)
            if payload and payload.get("sub"):
                try:
                    actor_caregiver_id = UUID(payload["sub"])
                except ValueError:
                    pass

        # Extract patient_id from path parameters if present
        patient_id: Optional[UUID] = None
        patient_id_path = request.path_params.get("patient_id")
        if patient_id_path:
            try:
                patient_id = UUID(str(patient_id_path))
            except ValueError:
                pass

        # Log event
        log_audit_event(
            db=db,
            action=action_name,
            actor_caregiver_id=actor_caregiver_id,
            patient_id=patient_id,
            metadata={"path": request.url.path, "method": request.method}
        )

    return dependency
