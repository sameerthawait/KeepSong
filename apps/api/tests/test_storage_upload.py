import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from main import app
from app.db import SessionLocal
from app.models import Caregiver, Patient, CaregiverPatientAccess, ConsentRecord, Recording, AuditLog
from app.core.security import get_password_hash, create_access_token
from app.core.storage import check_bucket_encryption

client = TestClient(app)



def test_mime_type_and_file_size_validation(clean_db: Session):
    c1 = Caregiver(email="upload_owner@example.com", password_hash=get_password_hash("pass"), name="Owner")
    clean_db.add(c1)
    clean_db.commit()

    p1 = Patient(name="Upload Patient", primary_caregiver_id=c1.id)
    clean_db.add(p1)
    clean_db.commit()

    token = create_access_token({"sub": str(c1.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Invalid MIME type rejected
    invalid_mime_res = client.post(
        f"/patients/{p1.id}/upload-url",
        json={"content_type": "application/x-msdownload", "file_size": 1024, "category": "audio"},
        headers=headers
    )
    assert invalid_mime_res.status_code == 400
    assert "Invalid audio file type" in invalid_mime_res.json()["detail"]

    # 2. Excessive file size (>50MB) rejected
    huge_file_res = client.post(
        f"/patients/{p1.id}/upload-url",
        json={"content_type": "audio/webm", "file_size": 60 * 1024 * 1024, "category": "audio"},
        headers=headers
    )
    assert huge_file_res.status_code == 400
    assert "exceeds maximum limit" in huge_file_res.json()["detail"]

    # 3. Valid audio request succeeds
    valid_res = client.post(
        f"/patients/{p1.id}/upload-url",
        json={"content_type": "audio/webm", "file_size": 5 * 1024 * 1024, "category": "audio", "filename": "test_recording.webm"},
        headers=headers
    )
    assert valid_res.status_code == 200
    data = valid_res.json()
    assert "upload_url" in data
    assert "asset_url" in data
    assert "test_recording.webm" in data["file_key"]

def test_recording_creation_pending_status(clean_db: Session):
    c1 = Caregiver(email="rec_owner@example.com", password_hash=get_password_hash("pass"), name="Owner")
    clean_db.add(c1)
    clean_db.flush()

    p1 = Patient(name="Recording Patient", primary_caregiver_id=c1.id)
    clean_db.add(p1)
    clean_db.flush()

    access = CaregiverPatientAccess(caregiver_id=c1.id, patient_id=p1.id, role="owner")
    clean_db.add(access)

    # Consent on file required
    consent = ConsentRecord(patient_id=p1.id, recorded_by_caregiver_id=c1.id, consent_basis="Signed consent")
    clean_db.add(consent)
    clean_db.commit()

    token = create_access_token({"sub": str(c1.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Create recording asset
    rec_res = client.post(
        f"/patients/{p1.id}/recordings",
        json={"audio_url": "https://storage.googleapis.com/keepsong-mock/audio1.mp3", "duration_seconds": 30},
        headers=headers
    )
    assert rec_res.status_code == 201
    r_data = rec_res.json()
    assert r_data["processing_status"] == "pending"
    assert r_data["patient_id"] == str(p1.id)

def test_bucket_encryption_active():
    status_info = check_bucket_encryption()
    assert status_info.get("encryption_active") is True
