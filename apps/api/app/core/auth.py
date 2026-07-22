from uuid import UUID
from typing import Callable, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Caregiver, CaregiverPatientAccess, Patient
from app.core.security import decode_token

security = HTTPBearer()

def get_current_caregiver(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Caregiver:
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if payload.get("refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cannot use refresh token as access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    caregiver_id_str = payload.get("sub")
    if not caregiver_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject identifier",
        )
        
    try:
        caregiver_id = UUID(caregiver_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid subject ID format",
        )

    caregiver = db.query(Caregiver).filter(Caregiver.id == caregiver_id).first()
    if not caregiver:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Caregiver account no longer exists",
        )
        
    return caregiver


def require_patient_access(required_role: str = "contributor") -> Callable:
    """
    Server-side RBAC dependency enforcing caregiver_patient_access check.
    Caregiver A cannot access Patient X's data without an access record,
    even with a guessed valid patient ID.
    """
    def dependency(
        patient_id: UUID,
        current_caregiver: Caregiver = Depends(get_current_caregiver),
        db: Session = Depends(get_db)
    ) -> CaregiverPatientAccess:
        # Check patient exists
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient record not found",
            )

        access = db.query(CaregiverPatientAccess).filter(
            CaregiverPatientAccess.caregiver_id == current_caregiver.id,
            CaregiverPatientAccess.patient_id == patient_id
        ).first()

        if not access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Caregiver has no authorization record for this patient.",
            )

        if required_role == "owner" and access.role != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Owner permissions required for this action on this patient.",
            )

        return access

    return dependency
