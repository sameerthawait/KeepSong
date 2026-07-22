import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from main import app
from app.db import SessionLocal
from app.models import Caregiver, Patient, CaregiverPatientAccess, ConsentRecord, Recording, Entity, EntityMention, FamilyMember, StoryPrompt, SuggestedPrompt, AuditLog
from app.core.security import get_password_hash, create_access_token
from app.ai.graph import extract_and_link_entities
from app.ai.embeddings import generate_embedding

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    try:
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
        db.close()

def test_entity_extraction_and_deduplication(clean_db: Session):
    c1 = Caregiver(email="kg_owner@example.com", password_hash=get_password_hash("pass"), name="Owner")
    clean_db.add(c1)
    clean_db.commit()

    p1 = Patient(name="KG Patient", primary_caregiver_id=c1.id)
    clean_db.add(p1)
    clean_db.commit()

    fm = FamilyMember(patient_id=p1.id, name="Sarah", relationship="Daughter")
    clean_db.add(fm)
    clean_db.commit()

    rec_id1 = uuid4()
    rec1 = Recording(id=rec_id1, patient_id=p1.id, audio_url="https://example.com/a1.mp3", processing_status="done")
    clean_db.add(rec1)
    clean_db.commit()

    res1 = extract_and_link_entities("Sarah came over for lunch today.", p1.id, rec_id1, clean_db)
    assert res1["entities_count"] >= 1

    entities = clean_db.query(Entity).filter(Entity.patient_id == p1.id).all()
    sarah_entity = [e for e in entities if e.name.lower() == "sarah"]
    assert len(sarah_entity) == 1

    rec_id2 = uuid4()
    rec2 = Recording(id=rec_id2, patient_id=p1.id, audio_url="https://example.com/a2.mp3", processing_status="done")
    clean_db.add(rec2)
    clean_db.commit()

    extract_and_link_entities("Sarah brought flowers on Sunday.", p1.id, rec_id2, clean_db)

    entities_after = clean_db.query(Entity).filter(Entity.patient_id == p1.id).all()
    sarah_entity_after = [e for e in entities_after if e.name.lower() == "sarah"]
    assert len(sarah_entity_after) == 1

    extract_and_link_entities("Sally is our neighbor.", p1.id, rec_id2, clean_db)
    assert len(clean_db.query(Entity).filter(Entity.patient_id == p1.id).all()) >= 1

def test_suggested_prompt_caregiver_approval_rule(clean_db: Session):
    c1 = Caregiver(email="prompt_owner@example.com", password_hash=get_password_hash("pass"), name="Owner")
    clean_db.add(c1)
    clean_db.commit()

    p1 = Patient(name="Prompt Patient", primary_caregiver_id=c1.id)
    clean_db.add(p1)
    clean_db.commit()

    access = CaregiverPatientAccess(caregiver_id=c1.id, patient_id=p1.id, role="owner")
    clean_db.add(access)
    clean_db.commit()

    token = create_access_token({"sub": str(c1.id)})
    headers = {"Authorization": f"Bearer {token}"}

    suggested = SuggestedPrompt(
        patient_id=p1.id,
        prompt_text="Last time you mentioned Buster. Would you like to share more about him?",
        is_approved=False
    )
    clean_db.add(suggested)
    clean_db.commit()

    patient_prompts_res = client.get(f"/patients/{p1.id}/prompts", headers=headers)
    assert patient_prompts_res.status_code == 200
    assert not any(p["prompt_text"] == suggested.prompt_text for p in patient_prompts_res.json())

    suggested_res = client.get(f"/patients/{p1.id}/suggested-prompts", headers=headers)
    assert suggested_res.status_code == 200
    assert len(suggested_res.json()) == 1

    approve_res = client.post(f"/patients/{p1.id}/suggested-prompts/{suggested.id}/approve", headers=headers)
    assert approve_res.status_code == 200
    assert approve_res.json()["prompt_text"] == suggested.prompt_text

    patient_prompts_after = client.get(f"/patients/{p1.id}/prompts", headers=headers)
    assert any(p["prompt_text"] == suggested.prompt_text for p in patient_prompts_after.json())

def test_advanced_sql_filtered_vector_search(clean_db: Session):
    c1 = Caregiver(email="filter_owner@example.com", password_hash=get_password_hash("pass"), name="Owner")
    clean_db.add(c1)
    clean_db.commit()

    p1 = Patient(name="Filter Patient", primary_caregiver_id=c1.id)
    clean_db.add(p1)
    clean_db.commit()

    access = CaregiverPatientAccess(caregiver_id=c1.id, patient_id=p1.id, role="owner")
    clean_db.add(access)
    clean_db.commit()

    rec1 = Recording(
        id=uuid4(),
        patient_id=p1.id,
        audio_url="https://example.com/1960.mp3",
        transcript="We got married in 1968.",
        theme="romance/wedding",
        estimated_decade="1960s",
        embedding=generate_embedding("We got married in 1968."),
        processing_status="done"
    )
    rec2 = Recording(
        id=uuid4(),
        patient_id=p1.id,
        audio_url="https://example.com/1980.mp3",
        transcript="We went on vacation in 1982.",
        theme="family",
        estimated_decade="1980s",
        embedding=generate_embedding("We went on vacation in 1982."),
        processing_status="done"
    )
    clean_db.add(rec1)
    clean_db.add(rec2)
    clean_db.commit()

    token = create_access_token({"sub": str(c1.id)})
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(f"/patients/{p1.id}/timeline/search?decade=1960s", headers=headers)
    assert res.status_code == 200
    results = res.json()
    assert len(results) == 1
    assert results[0]["estimated_decade"] == "1960s"

def test_multimodal_photo_caption_and_explainability(clean_db: Session):
    c1 = Caregiver(email="photo_owner@example.com", password_hash=get_password_hash("pass"), name="Owner")
    clean_db.add(c1)
    clean_db.commit()

    p1 = Patient(name="Photo Patient", primary_caregiver_id=c1.id)
    clean_db.add(p1)
    clean_db.commit()

    access = CaregiverPatientAccess(caregiver_id=c1.id, patient_id=p1.id, role="owner")
    clean_db.add(access)
    clean_db.commit()

    token = create_access_token({"sub": str(c1.id)})
    headers = {"Authorization": f"Bearer {token}"}

    photo_res = client.post(
        f"/patients/{p1.id}/photos/suggest-caption",
        json={"photo_url": "https://example.com/photo.jpg", "family_member_name": "Sarah", "relationship": "Daughter"},
        headers=headers
    )
    assert photo_res.status_code == 200
    p_data = photo_res.json()
    assert p_data["label"] == "AI suggestion — please review"
    assert "Sarah" in p_data["suggested_caption"]
