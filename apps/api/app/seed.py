import sys
import os
from sqlalchemy.orm import Session

# Add current folder to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import SessionLocal, engine, Base
from app.models import Caregiver, Patient, CaregiverPatientAccess, ConsentRecord, FamilyMember, StoryPrompt, Recording, AuditLog
from app.core.security import get_password_hash

def seed_db():
    db = SessionLocal()
    try:
        # Clear existing data in reverse dependency order
        db.query(AuditLog).delete()
        db.query(Recording).delete()
        db.query(StoryPrompt).delete()
        db.query(FamilyMember).delete()
        db.query(ConsentRecord).delete()
        db.query(CaregiverPatientAccess).delete()
        db.query(Patient).delete()
        db.query(Caregiver).delete()
        db.commit()
        print("Cleared database tables.")

        # Create Caregiver
        caregiver = Caregiver(
            email="caregiver@example.com",
            password_hash=get_password_hash("password123"),
            name="Jane Doe"
        )
        db.add(caregiver)
        db.flush()  # Populates caregiver.id

        # Create Patient
        patient = Patient(
            name="John Doe",
            pin_hash=get_password_hash("1234"),
            primary_caregiver_id=caregiver.id
        )
        db.add(patient)
        db.flush()  # Populates patient.id

        # Caregiver access
        access = CaregiverPatientAccess(
            caregiver_id=caregiver.id,
            patient_id=patient.id,
            role="owner"
        )
        db.add(access)

        # Consent record
        consent = ConsentRecord(
            patient_id=patient.id,
            recorded_by_caregiver_id=caregiver.id,
            consent_basis="Family proxy consent signed on paper on 2026-07-19."
        )
        db.add(consent)

        # Family member
        family_member = FamilyMember(
            patient_id=patient.id,
            name="Jane Doe",
            relationship="Daughter",
            photo_url="https://images.unsplash.com/photo-1544005313-94ddf0286df2"
        )
        db.add(family_member)

        # Story prompts
        prompt1 = StoryPrompt(
            patient_id=patient.id,
            prompt_text="Tell me about your favorite childhood pet.",
            sequence_order=1,
            is_custom=False
        )
        prompt2 = StoryPrompt(
            patient_id=patient.id,
            prompt_text="What was your first job, and what did you like about it?",
            sequence_order=2,
            is_custom=False
        )
        db.add(prompt1)
        db.add(prompt2)
        db.flush()

        # Recording
        recording = Recording(
            patient_id=patient.id,
            prompt_id=prompt1.id,
            audio_url="https://storage.googleapis.com/keepsong-mock/audio1.mp3",
            transcript="I had a dog named Buster when I was ten. He was a black retriever. He would follow me everywhere, even to the bus stop.",
            theme="childhood",
            estimated_decade="1960s",
            ai_caption="John shares a story about Buster, his retriever.",
            duration_seconds=42,
            processing_status="done"
        )
        db.add(recording)

        # Audit logs
        audit1 = AuditLog(
            actor_caregiver_id=caregiver.id,
            patient_id=patient.id,
            action="CREATE_PATIENT",
            action_metadata={"patient_name": "John Doe"}
        )
        audit2 = AuditLog(
            actor_caregiver_id=caregiver.id,
            patient_id=patient.id,
            action="RECORD_CONSENT",
            action_metadata={"basis": "proxy"}
        )
        db.add(audit1)
        db.add(audit2)

        db.commit()
        print("Successfully seeded the database!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
