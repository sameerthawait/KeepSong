import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.db import SessionLocal
from app.models import Caregiver, Patient, CaregiverPatientAccess, ConsentRecord, FamilyMember, StoryPrompt, Recording, AuditLog
from app.core.security import get_password_hash, create_access_token

client = TestClient(app)



def test_full_caregiver_dashboard_flow(clean_db: Session):
    # 1. Setup Owner Caregiver
    c1 = Caregiver(email="owner@example.com", password_hash=get_password_hash("pass123"), name="Owner Caregiver")
    clean_db.add(c1)
    clean_db.commit()

    token1 = create_access_token({"sub": str(c1.id)})
    headers1 = {"Authorization": f"Bearer {token1}"}

    # 2. Create Patient
    create_res = client.post("/patients", json={"name": "Mary Smith", "pin": "1234"}, headers=headers1)
    assert create_res.status_code == 201
    p_data = create_res.json()
    patient_id = p_data["id"]

    # 3. Add Family Member
    fm_res = client.post(f"/patients/{patient_id}/family-members", json={"name": "David Smith", "relationship": "Son"}, headers=headers1)
    assert fm_res.status_code == 201
    assert fm_res.json()["name"] == "David Smith"

    # 4. Add Story Prompt
    prompt_res = client.post(f"/patients/{patient_id}/prompts", json={"prompt_text": "Tell us about your wedding day."}, headers=headers1)
    assert prompt_res.status_code == 201
    assert prompt_res.json()["prompt_text"] == "Tell us about your wedding day."

    # 5. Record Required Consent (Non-skippable step)
    consent_res = client.post(f"/patients/{patient_id}/consent", json={"consent_basis": "Proxy consent signed by legal guardian."}, headers=headers1)
    assert consent_res.status_code == 201
    assert consent_res.json()["consent_basis"] == "Proxy consent signed by legal guardian."

    # Verify Consent Status
    consent_status_res = client.get(f"/patients/{patient_id}/consent", headers=headers1)
    assert consent_status_res.status_code == 200
    assert consent_status_res.json()["has_consent"] is True

    # 6. Add Test Recording
    rec = Recording(
        patient_id=patient_id,
        audio_url="https://storage.googleapis.com/keepsong-mock/audio1.mp3",
        transcript="We got married in June 1968 at St. Mary's church. It was a beautiful sunny afternoon.",
        theme="romance",
        estimated_decade="1960s",
        ai_caption="Mary recalls her wedding day in June 1968.",
        processing_status="done"
    )
    clean_db.add(rec)
    clean_db.commit()

    # 7. Fetch Timeline
    timeline_res = client.get(f"/patients/{patient_id}/timeline", headers=headers1)
    assert timeline_res.status_code == 200
    t_data = timeline_res.json()
    assert t_data["total_recordings"] == 1
    assert t_data["has_consent"] is True
    assert t_data["timeline"][0]["group_title"] == "1960s"

    # 8. Test Paraphrased Semantic Search (Query: "marriage ceremony" should match "married in June 1968")
    search_res = client.get(f"/patients/{patient_id}/timeline/search?q=marriage", headers=headers1)
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert len(search_data) == 1
    assert "married in June 1968" in search_data[0]["transcript"]

    # 9. Caregiver Invite Flow
    invite_res = client.post(f"/patients/{patient_id}/invite-caregiver", json={"role": "contributor"}, headers=headers1)
    assert invite_res.status_code == 200
    code = invite_res.json()["invite_code"]

    # Caregiver 2 registers & claims invite
    c2 = Caregiver(email="sibling@example.com", password_hash=get_password_hash("pass123"), name="Sibling Caregiver")
    clean_db.add(c2)
    clean_db.commit()

    token2 = create_access_token({"sub": str(c2.id)})
    headers2 = {"Authorization": f"Bearer {token2}"}

    claim_res = client.post("/patients/claim-invite", json={"invite_code": code}, headers=headers2)
    assert claim_res.status_code == 200
    assert claim_res.json()["role"] == "contributor"

    # Caregiver 2 CAN now access Mary Smith's timeline
    c2_timeline_res = client.get(f"/patients/{patient_id}/timeline", headers=headers2)
    assert c2_timeline_res.status_code == 200
    assert c2_timeline_res.json()["total_recordings"] == 1
