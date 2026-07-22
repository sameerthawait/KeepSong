import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from main import app
from app.db import SessionLocal
from app.models import Caregiver, Patient, CaregiverPatientAccess, ConsentRecord, Recording, AuditLog
from app.core.security import get_password_hash, create_access_token
from app.ai.embeddings import generate_embedding

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    try:
        db.query(AuditLog).delete()
        db.query(Recording).delete()
        db.query(ConsentRecord).delete()
        db.query(CaregiverPatientAccess).delete()
        db.query(Patient).delete()
        db.query(Caregiver).delete()
        db.commit()
        yield db
    finally:
        db.close()

def test_paraphrased_semantic_search(clean_db: Session):
    c1 = Caregiver(email="search_owner@example.com", password_hash=get_password_hash("pass"), name="Owner")
    clean_db.add(c1)
    clean_db.flush()

    p1 = Patient(name="Search Patient", primary_caregiver_id=c1.id)
    clean_db.add(p1)
    clean_db.flush()

    access = CaregiverPatientAccess(caregiver_id=c1.id, patient_id=p1.id, role="owner")
    clean_db.add(access)

    # Transcript uses "tied the knot" (does NOT contain "getting married")
    transcript_text = "We got married at St. Mary's church. It was the day we tied the knot in June 1968."
    vec = generate_embedding(transcript_text)

    rec = Recording(
        id=uuid4(),
        patient_id=p1.id,
        audio_url="https://storage.googleapis.com/keepsong-mock/wedding.mp3",
        transcript=transcript_text,
        theme="romance/wedding",
        estimated_decade="1960s",
        ai_caption="Recalls tying the knot at St. Mary's church in June 1968.",
        embedding=vec,
        processing_status="done"
    )
    clean_db.add(rec)
    clean_db.commit()

    token = create_access_token({"sub": str(c1.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Query using paraphrased concept "getting married"
    res = client.get(f"/patients/{p1.id}/timeline/search?q=getting+married", headers=headers)
    assert res.status_code == 200
    results = res.json()
    assert len(results) == 1
    assert "tied the knot" in results[0]["transcript"]

def test_patient_isolation_search(clean_db: Session):
    c1 = Caregiver(email="p1_owner@example.com", password_hash=get_password_hash("pass"), name="P1 Owner")
    clean_db.add(c1)
    clean_db.flush()

    p1 = Patient(name="Patient One", primary_caregiver_id=c1.id)
    p2 = Patient(name="Patient Two", primary_caregiver_id=c1.id)
    clean_db.add(p1)
    clean_db.add(p2)
    clean_db.flush()

    access1 = CaregiverPatientAccess(caregiver_id=c1.id, patient_id=p1.id, role="owner")
    access2 = CaregiverPatientAccess(caregiver_id=c1.id, patient_id=p2.id, role="owner")
    clean_db.add(access1)
    clean_db.add(access2)

    # Add recording to Patient Two
    rec_p2 = Recording(
        id=uuid4(),
        patient_id=p2.id,
        audio_url="https://storage.googleapis.com/keepsong-mock/p2.mp3",
        transcript="We got married in 1975.",
        theme="romance/wedding",
        embedding=generate_embedding("We got married in 1975."),
        processing_status="done"
    )
    clean_db.add(rec_p2)
    clean_db.commit()

    token = create_access_token({"sub": str(c1.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Search query under Patient One's scope MUST NOT return Patient Two's recording
    res_p1 = client.get(f"/patients/{p1.id}/timeline/search?q=married", headers=headers)
    assert res_p1.status_code == 200
    assert len(res_p1.json()) == 0
