import pytest
from sqlalchemy.orm import Session
from main import app
from app.db import SessionLocal, get_db
from app.models import Caregiver, Patient, Recording, AICallLog, AuditLog, ConsentRecord, CaregiverPatientAccess, StoryPrompt, FamilyMember, SuggestedPrompt, EntityMention, Entity

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
        db.query(AICallLog).delete()
        db.query(AuditLog).delete()
        db.query(SuggestedPrompt).delete()
        db.query(EntityMention).delete()
        db.query(Entity).delete()
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
        db.rollback()
        db.close()
        app.dependency_overrides.pop(get_db, None)
