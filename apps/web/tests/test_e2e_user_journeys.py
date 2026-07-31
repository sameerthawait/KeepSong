import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from main import app
from app.db import SessionLocal, get_db
from app.models import Caregiver, Patient, CaregiverPatientAccess, ConsentRecord, StoryPrompt, FamilyMember, Recording, AuditLog
from app.core.security import get_password_hash, create_access_token
from app.ai.embeddings import generate_embedding

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    
    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    try:
        db.query(AuditLog).delete()
        db.query(Recording).delete()
        db.query(StoryPrompt).delete()
        db.query(FamilyMember).delete()
        db.query(ConsentRecord).delete()
        db.query(CaregiverPatientAccess).delete()
        db.query(Patient).delete()
        db.query(Caregiver).delete()
        db.commit()
        yield db
    finally:
        db.close()

def test_e2e_patient_checkin_happy_path(clean_db: Session):
    c1 = Caregiver(email="patient_e2e@example.com", password_hash=get_password_hash("pass"), name="Caregiver")
    clean_db.add(c1)
    clean_db.commit()

    p1 = Patient(name="John Doe", pin_hash=get_password_hash("1234"), primary_caregiver_id=c1.id)
    clean_db.add(p1)
    clean_db.commit()

    access = CaregiverPatientAccess(caregiver_id=c1.id, patient_id=p1.id, role="owner")
    consent = ConsentRecord(patient_id=p1.id, recorded_by_caregiver_id=c1.id, consent_basis="Proxy consent")
    clean_db.add(access)
    clean_db.add(consent)
    clean_db.commit()

    # 1. Verify Patient PIN
    pin_res = client.post("/auth/patient/verify-pin", json={"patient_id": str(p1.id), "pin": "1234"})
    assert pin_res.status_code == 200
    assert "access_token" in pin_res.json()

    # 2. Fetch Check-In single-screen payload
    checkin_res = client.get(f"/patients/{p1.id}/checkin")
    assert checkin_res.status_code == 200
    c_data = checkin_res.json()
    assert c_data["patient_name"] == "John Doe"
    assert c_data["has_consent"] is True
    assert "weather" in c_data
    assert "family_member" in c_data

    # 3. Direct upload URL & Recording creation
    upload_res = client.post(f"/patients/{p1.id}/upload-url", json={"content_type": "audio/webm", "file_size": 1024, "category": "audio"})
    assert upload_res.status_code == 200

    rec_res = client.post(f"/patients/{p1.id}/recordings", json={"audio_url": upload_res.json()["asset_url"]})
    assert rec_res.status_code == 201
    assert rec_res.json()["processing_status"] == "pending"

def test_e2e_caregiver_setup_and_consent_flow(clean_db: Session):
    """
    E2E Caregiver Setup Journey:
    Caregiver registration -> patient profile creation -> family member upload -> required consent capture.
    """
    reg_res = client.post("/auth/caregiver/register", json={"email": "e2e_cg@example.com", "password": "Password123!", "name": "Sarah CG"})
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_p_res = client.post("/patients", json={"name": "Mary Smith", "pin": "5678"}, headers=headers)
    assert create_p_res.status_code == 201
    patient_id = create_p_res.json()["id"]

    fm_res = client.post(f"/patients/{patient_id}/family-members", json={"name": "David Smith", "relationship": "Son"}, headers=headers)
    assert fm_res.status_code == 201

    consent_res = client.post(f"/patients/{patient_id}/consent", json={"consent_basis": "Signed legal consent form"}, headers=headers)
    assert consent_res.status_code == 201

def test_e2e_semantic_timeline_search(clean_db: Session):
    """
    E2E Semantic Search Journey:
    Caregiver searches "getting married" -> finds recording with transcript "tied the knot".
    """
    c1 = Caregiver(email="search_e2e@example.com", password_hash=get_password_hash("pass"), name="Caregiver")
    clean_db.add(c1)
    clean_db.commit()

    p1 = Patient(name="Mary Smith", primary_caregiver_id=c1.id)
    clean_db.add(p1)
    clean_db.commit()

    access = CaregiverPatientAccess(caregiver_id=c1.id, patient_id=p1.id, role="owner")
    clean_db.add(access)

    rec = Recording(
        id=uuid4(),
        patient_id=p1.id,
        audio_url="https://example.com/audio.mp3",
        transcript="We got married at St. Mary's. It was the day we tied the knot in 1968.",
        theme="romance/wedding",
        estimated_decade="1960s",
        embedding=generate_embedding("We got married at St. Mary's. It was the day we tied the knot in 1968."),
        processing_status="done"
    )
    clean_db.add(rec)
    clean_db.commit()

    token = create_access_token({"sub": str(c1.id)})
    headers = {"Authorization": f"Bearer {token}"}

    search_res = client.get(f"/patients/{p1.id}/timeline/search?q=getting+married", headers=headers)
    assert search_res.status_code == 200
    assert len(search_res.json()) == 1
    assert "tied the knot" in search_res.json()[0]["transcript"]
