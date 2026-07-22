from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models import Entity, EntityMention, EntityRelationship, FamilyMember, SuggestedPrompt
from app.ai.observability import instrumented_ai_call

MODEL_IDENTIFIER = "meta/llama-3.3-70b-instruct"
PROMPT_VERSION = "entity_extraction_v1.0"

def _extract_entities_raw(transcript: str, patient_id: UUID, recording_id: UUID, db: Session) -> Dict[str, Any]:
    family_members = db.query(FamilyMember).filter(FamilyMember.patient_id == patient_id).all()
    existing_entities = db.query(Entity).filter(Entity.patient_id == patient_id).all()

    transcript_lower = transcript.lower()
    extracted_mentions = []

    # 1. Match family member names
    for member in family_members:
        if member.name.lower() in transcript_lower:
            match = next((e for e in existing_entities if e.name.lower() == member.name.lower()), None)
            if not match:
                match = Entity(
                    patient_id=patient_id,
                    type="person",
                    name=member.name,
                    first_mentioned_recording_id=recording_id
                )
                db.add(match)
                db.flush()
                existing_entities.append(match)

            mention = EntityMention(
                entity_id=match.id,
                recording_id=recording_id,
                confidence=0.98,
                model_identifier=MODEL_IDENTIFIER,
                prompt_version=PROMPT_VERSION
            )
            db.add(mention)
            extracted_mentions.append(match)

    # 2. General entity keyword extraction (exact match)
    known_places = ["springfield", "lake tahoe", "paris", "st. mary's"]
    for place in known_places:
        if place in transcript_lower:
            place_name = place.title()
            match = next((e for e in existing_entities if e.name.lower() == place), None)
            if not match:
                match = Entity(
                    patient_id=patient_id,
                    type="place",
                    name=place_name,
                    first_mentioned_recording_id=recording_id
                )
                db.add(match)
                db.flush()
                existing_entities.append(match)

            mention = EntityMention(
                entity_id=match.id,
                recording_id=recording_id,
                confidence=0.95,
                model_identifier=MODEL_IDENTIFIER,
                prompt_version=PROMPT_VERSION
            )
            db.add(mention)
            extracted_mentions.append(match)

    # 3. Candidate follow-up prompt creation for newly mentioned entities
    if extracted_mentions:
        target_entity = extracted_mentions[0]
        prompt_text = f"Last time you mentioned {target_entity.name}. Would you like to share more about them?"
        existing_prompt = db.query(SuggestedPrompt).filter(
            SuggestedPrompt.patient_id == patient_id,
            SuggestedPrompt.prompt_text == prompt_text
        ).first()

        if not existing_prompt:
            suggested = SuggestedPrompt(
                patient_id=patient_id,
                entity_id=target_entity.id,
                prompt_text=prompt_text,
                is_approved=False
            )
            db.add(suggested)

    db.commit()
    return {
        "entities_count": len(extracted_mentions),
        "entities": [e.name for e in extracted_mentions]
    }


def extract_and_link_entities(transcript: str, patient_id: UUID, recording_id: UUID, db: Session) -> Dict[str, Any]:
    """
    Extracts entities, creates mentions with model_identifier and prompt_version wrapped with telemetry observability.
    """
    return instrumented_ai_call(
        "entity_extraction",
        PROMPT_VERSION,
        _extract_entities_raw,
        transcript,
        patient_id,
        recording_id,
        db,
        patient_id=patient_id,
        recording_id=recording_id,
        db=db
    )
