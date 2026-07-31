from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.db import get_db
from app.models import Caregiver, Patient
from app.schemas import (
    CaregiverRegister,
    CaregiverLogin,
    TokenResponse,
    TokenRefresh,
    CaregiverOut,
    PatientPinVerify,
    PatientTokenResponse
)
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.core.rate_limit import pin_rate_limiter
from app.core.audit import log_audit_event

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/caregiver/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_caregiver(payload: CaregiverRegister, db: Session = Depends(get_db)):
    existing = db.query(Caregiver).filter(Caregiver.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    caregiver = Caregiver(
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        name=payload.name
    )
    db.add(caregiver)
    db.commit()
    db.refresh(caregiver)

    log_audit_event(
        db=db,
        action="REGISTER_CAREGIVER",
        actor_caregiver_id=caregiver.id,
        metadata={"email": caregiver.email}
    )

    access_token = create_access_token({"sub": str(caregiver.id)})
    refresh_token = create_refresh_token({"sub": str(caregiver.id)})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/caregiver/login", response_model=TokenResponse)
def login_caregiver(payload: CaregiverLogin, db: Session = Depends(get_db)):
    caregiver = db.query(Caregiver).filter(Caregiver.email == payload.email).first()
    if not caregiver or not verify_password(payload.password, caregiver.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    log_audit_event(
        db=db,
        action="LOGIN_CAREGIVER",
        actor_caregiver_id=caregiver.id,
        metadata={"email": caregiver.email}
    )

    access_token = create_access_token({"sub": str(caregiver.id)})
    refresh_token = create_refresh_token({"sub": str(caregiver.id)})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/caregiver/refresh", response_model=TokenResponse)
def refresh_token(payload: TokenRefresh, db: Session = Depends(get_db)):
    decoded = decode_token(payload.refresh_token)
    if not decoded or not decoded.get("refresh") or not decoded.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    caregiver_id_str = decoded.get("sub")
    caregiver = db.query(Caregiver).filter(Caregiver.id == UUID(caregiver_id_str)).first()
    if not caregiver:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Caregiver account no longer exists",
        )

    new_access_token = create_access_token({"sub": str(caregiver.id)})
    new_refresh_token = create_refresh_token({"sub": str(caregiver.id)})

    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)


@router.post("/patient/verify-pin", response_model=PatientTokenResponse)
def verify_patient_pin(payload: PatientPinVerify, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        patient = db.query(Patient).first()

    # If database has no patients yet, create default demo patient
    if not patient:
        patient = Patient(
            name="Grandma Eleanor",
            pin_hash=hash_password("1234"),
            has_consent=True
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)

    patient_id_str = str(patient.id)
    
    # Check rate limit before verifying
    pin_rate_limiter.check_rate_limit(patient_id_str)

    if not patient.pin_hash or not verify_password(payload.pin, patient.pin_hash):
        # Record failed attempt for rate limiting
        pin_rate_limiter.record_attempt(patient_id_str)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid patient PIN",
        )

    # Success: reset rate limit attempts for this patient
    pin_rate_limiter.reset(patient_id_str)

    # Create scoped patient token
    patient_token = create_access_token({"sub_patient": str(patient.id)})

    log_audit_event(
        db=db,
        action="PATIENT_PIN_LOGIN",
        patient_id=patient.id,
        metadata={"patient_name": patient.name}
    )

    return PatientTokenResponse(access_token=patient_token, patient_id=patient.id, patient_name=patient.name)
