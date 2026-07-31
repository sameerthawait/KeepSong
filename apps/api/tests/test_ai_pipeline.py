import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from main import app
from app.db import SessionLocal
from app.models import Caregiver, Patient, CaregiverPatientAccess, ConsentRecord, Recording, AuditLog
from app.core.security import get_password_hash, create_access_token
from app.ai.pipeline import run_ai_pipeline

client = TestClient(app)

@pytest.fixture(autouse=True)


def test_full_ai_pipeline_happy_path(clean_db: Session):
    c1 = Caregiver(email="ai_owner@example.com", password_hash=get_password_hash("pass"), name="Owner")
    clean_db.add(c1)
    clean_db.flush()

    p1 = Patient(name="AI Patient", primary_caregiver_id=c1.id)
    clean_db.add(p1)
    clean_db.flush()

    rec_id = uuid4()
    rec = Recording(
        id=rec_id,
        patient_id=p1.id,
        audio_url="https://storage.googleapis.com/keepsong-mock/audio1.mp3",
        processing_status="pending"
    )
    clean_db.add(rec)
    clean_db.commit()

    # Execute pipeline
    result = run_ai_pipeline(rec_id, clean_db)
    assert result is not None
    assert result.processing_status == "done"
    assert result.transcript is not None
    assert "Buster" in result.transcript
    assert result.theme == "childhood"
    assert result.estimated_decade == "1960s"
    assert result.ai_caption is not None
    assert result.classification_confidence >= 0.70
    from app.core.config import settings
    assert result.model_identifier in (settings.NIM_MODEL, "meta/llama-3.3-70b-instruct", "meta/llama-3.1-8b-instruct")
    assert result.prompt_version == "classification_v1.0"

def test_asr_failure_simulation_and_retry(clean_db: Session):
    c1 = Caregiver(email="asr_fail@example.com", password_hash=get_password_hash("pass"), name="Owner")
    clean_db.add(c1)
    clean_db.flush()

    p1 = Patient(name="ASR Fail Patient", primary_caregiver_id=c1.id)
    clean_db.add(p1)
    clean_db.flush()

    access = CaregiverPatientAccess(caregiver_id=c1.id, patient_id=p1.id, role="owner")
    clean_db.add(access)

    rec_id = uuid4()
    rec = Recording(
        id=rec_id,
        patient_id=p1.id,
        audio_url="https://storage.googleapis.com/keepsong-mock/audio1.mp3",
        processing_status="pending"
    )
    clean_db.add(rec)
    clean_db.commit()

    # Simulate ASR failure
    result = run_ai_pipeline(rec_id, clean_db, force_asr_fail=True)
    assert result.processing_status == "failed"
    assert result.failure_stage == "asr"
    assert result.audio_url == "https://storage.googleapis.com/keepsong-mock/audio1.mp3"  # Audio preserved

    # Caregiver triggers retry endpoint
    token = create_access_token({"sub": str(c1.id)})
    retry_res = client.post(
        f"/patients/{p1.id}/recordings/{rec_id}/retry",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert retry_res.status_code == 200
    assert retry_res.json()["processing_status"] == "pending"

def test_malformed_llm_json_fallback(clean_db: Session):
    c1 = Caregiver(email="llm_fallback@example.com", password_hash=get_password_hash("pass"), name="Owner")
    clean_db.add(c1)
    clean_db.flush()

    p1 = Patient(name="LLM Fallback Patient", primary_caregiver_id=c1.id)
    clean_db.add(p1)
    clean_db.flush()

    rec_id = uuid4()
    rec = Recording(
        id=rec_id,
        patient_id=p1.id,
        audio_url="https://storage.googleapis.com/keepsong-mock/audio1.mp3",
        processing_status="pending"
    )
    clean_db.add(rec)
    clean_db.commit()

    # Simulate malformed LLM response
    result = run_ai_pipeline(rec_id, clean_db, force_llm_malformed=True)
    assert result.processing_status == "done"
    assert result.theme == "uncategorized"
    assert result.estimated_decade == "Unknown"
