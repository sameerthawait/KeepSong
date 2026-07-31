import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from main import app
from app.db import SessionLocal
from app.models import Caregiver, Patient, CaregiverPatientAccess, ConsentRecord, Recording, AuditLog
from app.core.security import get_password_hash, create_access_token

client = TestClient(app)



def test_caregiver_register_and_login(clean_db: Session):
    # Register
    reg_res = client.post("/auth/caregiver/register", json={
        "email": "testcaregiver@example.com",
        "password": "Password123!",
        "name": "Jane Doe"
    })
    assert reg_res.status_code == 201
    assert "access_token" in reg_res.json()
    assert "refresh_token" in reg_res.json()

    # Login
    login_res = client.post("/auth/caregiver/login", json={
        "email": "testcaregiver@example.com",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

def test_token_refresh(clean_db: Session):
    reg_res = client.post("/auth/caregiver/register", json={
        "email": "refresh@example.com",
        "password": "Password123!",
        "name": "Refresh User"
    })
    refresh_token = reg_res.json()["refresh_token"]

    ref_res = client.post("/auth/caregiver/refresh", json={"refresh_token": refresh_token})
    assert ref_res.status_code == 200
    assert "access_token" in ref_res.json()

def test_expired_token_rejection():
    res = client.get("/patients", headers={"Authorization": "Bearer invalid_or_expired_token"})
    assert res.status_code == 401

def test_exhaustive_rbac_boundary_isolation_matrix(clean_db: Session):
    """
    EXHAUSTIVE RBAC MATRIX TEST:
    Caregiver A owns Patient X. Caregiver B has NO access to Patient X.
    Verifies that EVERY patient-scoped endpoint explicitly blocks Caregiver B with 403 Forbidden.
    """
    c_a = Caregiver(email="cg_a@example.com", password_hash=get_password_hash("pass"), name="Caregiver A")
    c_b = Caregiver(email="cg_b@example.com", password_hash=get_password_hash("pass"), name="Caregiver B")
    clean_db.add(c_a)
    clean_db.add(c_b)
    clean_db.commit()

    p_x = Patient(name="Patient X", primary_caregiver_id=c_a.id)
    clean_db.add(p_x)
    clean_db.commit()

    access_a = CaregiverPatientAccess(caregiver_id=c_a.id, patient_id=p_x.id, role="owner")
    clean_db.add(access_a)
    clean_db.commit()

    token_b = create_access_token({"sub": str(c_b.id)})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    patient_scoped_endpoints = [
        ("GET", f"/patients/{p_x.id}"),
        ("POST", f"/patients/{p_x.id}/family-members", {"name": "Test", "relationship": "Son"}),
        ("GET", f"/patients/{p_x.id}/family-members"),
        ("POST", f"/patients/{p_x.id}/prompts", {"prompt_text": "Test prompt"}),
        ("GET", f"/patients/{p_x.id}/prompts"),
        ("POST", f"/patients/{p_x.id}/consent", {"consent_basis": "Proxy consent"}),
        ("GET", f"/patients/{p_x.id}/consent"),
        ("GET", f"/patients/{p_x.id}/timeline"),
        ("GET", f"/patients/{p_x.id}/timeline/search?q=test"),
        ("GET", f"/patients/{p_x.id}/graph"),
        ("GET", f"/patients/{p_x.id}/suggested-prompts"),
        ("POST", f"/patients/{p_x.id}/photos/suggest-caption", {"photo_url": "https://example.com/p.jpg"}),
        ("POST", f"/patients/{p_x.id}/invite-caregiver", {"role": "contributor"}),
    ]

    for method, path, *payload in patient_scoped_endpoints:
        body = payload[0] if payload else None
        if method == "GET":
            res = client.get(path, headers=headers_b)
        elif method == "POST":
            res = client.post(path, json=body, headers=headers_b)

        assert res.status_code == 403, f"RBAC BREACH DETECTED: {method} {path} returned {res.status_code} instead of 403 Forbidden!"

def test_pin_verification_rate_limiting(clean_db: Session):
    c1 = Caregiver(email="pin_owner@example.com", password_hash=get_password_hash("pass"), name="Owner Caregiver")
    clean_db.add(c1)
    clean_db.commit()

    p1 = Patient(name="PIN Rate Limit Patient", pin_hash=get_password_hash("1234"), primary_caregiver_id=c1.id)
    clean_db.add(p1)
    clean_db.commit()

    # Fail PIN verification 5 times
    for i in range(5):
        fail_res = client.post("/auth/patient/verify-pin", json={"patient_id": str(p1.id), "pin": "9999"})
        assert fail_res.status_code == 401

    # 6th attempt must trigger Rate Limit 429
    rate_res = client.post("/auth/patient/verify-pin", json={"patient_id": str(p1.id), "pin": "1234"})
    assert rate_res.status_code == 429
    assert "Too many verification attempts" in rate_res.json()["detail"]

def test_recording_access_produces_audit_log(clean_db: Session):
    c1 = Caregiver(email="audit_c1@example.com", password_hash=get_password_hash("pass"), name="Audit Caregiver")
    clean_db.add(c1)
    clean_db.commit()

    p1 = Patient(name="Audit Patient", primary_caregiver_id=c1.id)
    clean_db.add(p1)
    clean_db.commit()

    access = CaregiverPatientAccess(caregiver_id=c1.id, patient_id=p1.id, role="owner")
    clean_db.add(access)
    clean_db.commit()

    rec_id = uuid4()
    rec = Recording(
        id=rec_id,
        patient_id=p1.id,
        audio_url="https://example.com/audio.mp3",
        transcript="Sensitive transcript text",
        processing_status="done"
    )
    clean_db.add(rec)
    clean_db.commit()

    token = create_access_token({"sub": str(c1.id)})

    audit_count_before = clean_db.query(AuditLog).filter(AuditLog.action == "VIEW_RECORDING_TRANSCRIPT").count()
    assert audit_count_before == 0

    res = client.get(f"/patients/{p1.id}/recordings/{rec_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

    audit_logs = clean_db.query(AuditLog).filter(AuditLog.action == "VIEW_RECORDING_TRANSCRIPT").all()
    assert len(audit_logs) == 1
    assert audit_logs[0].actor_caregiver_id == c1.id
    assert audit_logs[0].patient_id == p1.id
