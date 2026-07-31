import pytest
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Caregiver, Patient, CaregiverPatientAccess, ConsentRecord, FamilyMember, StoryPrompt, Recording, AuditLog
from app.core.security import get_password_hash

def test_patient_deletion_keeps_audit_logs_and_cascades_others(clean_db: Session):
    db = clean_db
    # 1. Setup Caregiver, Patient and dependencies
    caregiver = Caregiver(
        email="test_caregiver@example.com",
        password_hash=get_password_hash("password"),
        name="Test Caregiver"
    )
    db.add(caregiver)
    db.flush()

    patient = Patient(
        name="Test Patient",
        pin_hash=get_password_hash("1111"),
        primary_caregiver_id=caregiver.id
    )
    db.add(patient)
    db.flush()

    # Access record
    access = CaregiverPatientAccess(
        caregiver_id=caregiver.id,
        patient_id=patient.id,
        role="owner"
    )
    db.add(access)

    # Consent
    consent = ConsentRecord(
        patient_id=patient.id,
        recorded_by_caregiver_id=caregiver.id,
        consent_basis="Implied test consent"
    )
    db.add(consent)

    # Family member
    family_member = FamilyMember(
        patient_id=patient.id,
        name="Family Member",
        relationship="Sibling"
    )
    db.add(family_member)

    # Prompt
    prompt = StoryPrompt(
        patient_id=patient.id,
        prompt_text="Test prompt text"
    )
    db.add(prompt)
    db.flush()

    # Audit log (retained - no FK cascade)
    audit = AuditLog(
        actor_caregiver_id=caregiver.id,
        patient_id=patient.id,
        action="TEST_ACTION",
        action_metadata={"foo": "bar"}
    )
    db.add(audit)
    db.commit()

    # Confirm insertion
    assert db.query(Patient).count() == 1
    assert db.query(CaregiverPatientAccess).count() == 1
    assert db.query(ConsentRecord).count() == 1
    assert db.query(FamilyMember).count() == 1
    assert db.query(StoryPrompt).count() == 1
    assert db.query(AuditLog).count() == 1

    # 2. Delete Patient
    db.delete(patient)
    db.commit()

    # 3. Verify Cascading & Retention
    # Patient should be gone
    assert db.query(Patient).count() == 0

    # Dependencies with FK ON DELETE CASCADE should be gone
    assert db.query(CaregiverPatientAccess).count() == 0
    assert db.query(ConsentRecord).count() == 0
    assert db.query(FamilyMember).count() == 0
    assert db.query(StoryPrompt).count() == 0

    # AuditLog should remain! (patient_id will still have the UUID value of the deleted patient)
    assert db.query(AuditLog).count() == 1
    retained_audit = db.query(AuditLog).first()
    assert retained_audit.patient_id == patient.id
    assert retained_audit.action == "TEST_ACTION"
