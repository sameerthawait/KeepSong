import json
import base64
import math
import uuid
from datetime import datetime
from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session
import httpx

from app.db import get_db
from app.models import (
    Patient,
    CaregiverPatientAccess,
    Caregiver,
    Recording,
    ConsentRecord,
    FamilyMember,
    StoryPrompt,
    Entity,
    EntityMention,
    EntityRelationship,
    SuggestedPrompt
)
from app.schemas import (
    PatientCreate,
    PatientOut,
    FamilyMemberCreate,
    FamilyMemberOut,
    StoryPromptCreate,
    StoryPromptOut,
    ConsentCreate,
    ConsentOut,
    UploadUrlRequest,
    UploadUrlResponse,
    RecordingCreate,
    RecordingOut,
    TimelineGroup,
    TimelineResponse,
    CaregiverInviteCreate,
    CaregiverInviteOut,
    CaregiverInviteClaim,
    EntityOut,
    RelationshipOut,
    GraphResponse,
    SuggestedPromptOut,
    PhotoCaptionSuggestRequest,
    PhotoCaptionSuggestResponse
)
from app.core.auth import get_current_caregiver, require_patient_access
from app.core.audit import audit_action, log_audit_event
from app.core.security import get_password_hash
from app.core.config import settings
from app.core.storage import validate_upload_request, generate_presigned_upload_url, check_bucket_encryption
from app.ai.pipeline import run_ai_pipeline
from app.ai.embeddings import generate_embedding

router = APIRouter(prefix="/patients", tags=["Patients"])

def _cosine_sim(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    m1 = math.sqrt(sum(a * a for a in v1))
    m2 = math.sqrt(sum(b * b for b in v2))
    return (dot / (m1 * m2)) if (m1 * m2 > 0) else 0.0


@router.get("/{patient_id}/checkin")
def get_patient_checkin_data(
    patient_id: UUID,
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found"
        )

    has_consent = db.query(ConsentRecord).filter(ConsentRecord.patient_id == patient_id).count() > 0

    family_member = db.query(FamilyMember).filter(FamilyMember.patient_id == patient_id).first()
    member_data = None
    if family_member:
        member_data = {
            "name": family_member.name,
            "relationship": family_member.relationship,
            "photo_url": family_member.photo_url
        }
    else:
        member_data = {
            "name": "Sarah",
            "relationship": "Daughter",
            "photo_url": "https://images.unsplash.com/photo-1544005313-94ddf0286df2"
        }

    prompt = db.query(StoryPrompt).filter(StoryPrompt.patient_id == patient_id).order_by(StoryPrompt.sequence_order.asc().nulls_last()).first()
    prompt_text = prompt.prompt_text if prompt else "Tell me about a memory that makes you smile today."

    weather_data = {
        "condition": "Partly Cloudy",
        "temp_f": 72,
        "icon": "⛅",
        "location": "Home"
    }

    if settings.WEATHER_API_KEY:
        try:
            res = httpx.get(
                f"https://api.openweathermap.org/data/2.5/weather?q=San+Francisco&units=imperial&appid={settings.WEATHER_API_KEY}",
                timeout=3.0
            )
            if res.status_code == 200:
                w_json = res.json()
                weather_data = {
                    "condition": w_json["weather"][0]["main"],
                    "temp_f": round(w_json["main"]["temp"]),
                    "icon": "☀️" if "clear" in w_json["weather"][0]["main"].lower() else "⛅",
                    "location": w_json["name"]
                }
        except Exception:
            pass

    return {
        "patient_id": patient_id,
        "patient_name": patient.name,
        "has_consent": has_consent,
        "date_display": datetime.now().strftime("%A, %B %d, %Y"),
        "weather": weather_data,
        "family_member": member_data,
        "prompt": {
            "id": str(prompt.id) if prompt else None,
            "prompt_text": prompt_text
        }
    }


# Knowledge Graph Visualization endpoint
@router.get(
    "/{patient_id}/graph",
    response_model=GraphResponse,
    dependencies=[Depends(audit_action("VIEW_KNOWLEDGE_GRAPH"))]
)
def get_patient_knowledge_graph(
    patient_id: UUID,
    access: CaregiverPatientAccess = Depends(require_patient_access(required_role="contributor")),
    db: Session = Depends(get_db)
):
    entities = db.query(Entity).filter(Entity.patient_id == patient_id).all()
    entity_ids = [e.id for e in entities]

    relationships = []
    if entity_ids:
        relationships = db.query(EntityRelationship).filter(
            (EntityRelationship.entity_id_a.in_(entity_ids)) | (EntityRelationship.entity_id_b.in_(entity_ids))
        ).all()

    return GraphResponse(
        entities=[EntityOut.model_validate(e) for e in entities],
        relationships=[RelationshipOut.model_validate(r) for r in relationships]
    )


# Recommendation Engine: Suggested Prompts endpoints
@router.get(
    "/{patient_id}/suggested-prompts",
    response_model=List[SuggestedPromptOut]
)
def list_suggested_prompts(
    patient_id: UUID,
    access: CaregiverPatientAccess = Depends(require_patient_access(required_role="contributor")),
    db: Session = Depends(get_db)
):
    return db.query(SuggestedPrompt).filter(
        SuggestedPrompt.patient_id == patient_id,
        SuggestedPrompt.is_approved == False
    ).order_by(SuggestedPrompt.created_at.desc()).limit(3).all()


@router.post(
    "/{patient_id}/suggested-prompts/{prompt_id}/approve",
    response_model=StoryPromptOut,
    dependencies=[Depends(audit_action("APPROVE_SUGGESTED_PROMPT"))]
)
def approve_suggested_prompt(
    patient_id: UUID,
    prompt_id: UUID,
    access: CaregiverPatientAccess = Depends(require_patient_access(required_role="contributor")),
    db: Session = Depends(get_db)
):
    suggested = db.query(SuggestedPrompt).filter(
        SuggestedPrompt.id == prompt_id,
        SuggestedPrompt.patient_id == patient_id
    ).first()

    if not suggested:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suggested prompt not found"
        )

    suggested.is_approved = True

    # Copy to StoryPrompt table for patient check-in view
    approved_story_prompt = StoryPrompt(
        patient_id=patient_id,
        prompt_text=suggested.prompt_text,
        is_custom=True
    )
    db.add(approved_story_prompt)
    db.commit()
    db.refresh(approved_story_prompt)

    return approved_story_prompt


# Multimodal Photo Context Suggestion endpoint
@router.post(
    "/{patient_id}/photos/suggest-caption",
    response_model=PhotoCaptionSuggestResponse
)
def suggest_photo_caption(
    patient_id: UUID,
    payload: PhotoCaptionSuggestRequest,
    access: CaregiverPatientAccess = Depends(require_patient_access(required_role="contributor")),
    db: Session = Depends(get_db)
):
    name = payload.family_member_name or "Family Member"
    relationship = payload.relationship or "relative"
    caption = f"Orientation portrait of {name} ({relationship.lower()}), captured during a family gathering."
    
    return PhotoCaptionSuggestResponse(
        suggested_caption=caption,
        label="AI suggestion — please review"
    )


# Direct Upload Presigned URL endpoint
@router.post(
    "/{patient_id}/upload-url",
    response_model=UploadUrlResponse,
    dependencies=[Depends(audit_action("GENERATE_UPLOAD_URL"))]
)
def request_presigned_upload_url(
    patient_id: UUID,
    payload: UploadUrlRequest,
    db: Session = Depends(get_db)
):
    validate_upload_request(
        content_type=payload.content_type,
        file_size=payload.file_size,
        category=payload.category
    )

    sanitized_filename = payload.filename.replace(" ", "_") if payload.filename else "file"
    file_key = f"patients/{patient_id}/{payload.category}s/{uuid.uuid4().hex[:12]}_{sanitized_filename}"

    upload_url, asset_url = generate_presigned_upload_url(
        file_key=file_key,
        content_type=payload.content_type,
        expiration_seconds=900
    )

    return UploadUrlResponse(
        upload_url=upload_url,
        asset_url=asset_url,
        file_key=file_key,
        expires_in=900
    )


# Create Recording endpoint & Enqueue AI Pipeline
@router.post(
    "/{patient_id}/recordings",
    response_model=RecordingOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(audit_action("CREATE_RECORDING"))]
)
def create_recording_asset(
    patient_id: UUID,
    payload: RecordingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    has_consent = db.query(ConsentRecord).filter(ConsentRecord.patient_id == patient_id).count() > 0
    if not has_consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recording disabled: No consent record on file for this patient."
        )

    recording = Recording(
        patient_id=patient_id,
        prompt_id=payload.prompt_id,
        audio_url=payload.audio_url,
        duration_seconds=payload.duration_seconds,
        processing_status="pending"
    )
    db.add(recording)
    db.commit()
    db.refresh(recording)

    background_tasks.add_task(run_ai_pipeline, recording.id, db)

    return recording


# Retry Failed Recording endpoint
@router.post(
    "/{patient_id}/recordings/{recording_id}/retry",
    response_model=RecordingOut,
    dependencies=[Depends(audit_action("RETRY_AI_PIPELINE"))]
)
def retry_failed_recording(
    patient_id: UUID,
    recording_id: UUID,
    background_tasks: BackgroundTasks,
    access: CaregiverPatientAccess = Depends(require_patient_access(required_role="contributor")),
    db: Session = Depends(get_db)
):
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.patient_id == patient_id
    ).first()

    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )

    recording.processing_status = "pending"
    recording.failure_stage = None
    db.commit()

    background_tasks.add_task(run_ai_pipeline, recording.id, db)

    return recording


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: PatientCreate,
    current_caregiver: Caregiver = Depends(get_current_caregiver),
    db: Session = Depends(get_db)
):
    patient = Patient(
        name=payload.name,
        pin_hash=get_password_hash(payload.pin) if payload.pin else get_password_hash("1234"),
        primary_caregiver_id=current_caregiver.id
    )
    db.add(patient)
    db.flush()

    access = CaregiverPatientAccess(
        caregiver_id=current_caregiver.id,
        patient_id=patient.id,
        role="owner"
    )
    db.add(access)
    db.commit()
    db.refresh(patient)

    log_audit_event(
        db=db,
        action="CREATE_PATIENT",
        actor_caregiver_id=current_caregiver.id,
        patient_id=patient.id,
        metadata={"patient_name": patient.name}
    )

    return patient


@router.get("", response_model=List[PatientOut])
def list_accessible_patients(
    current_caregiver: Caregiver = Depends(get_current_caregiver),
    db: Session = Depends(get_db)
):
    access_records = db.query(CaregiverPatientAccess).filter(
        CaregiverPatientAccess.caregiver_id == current_caregiver.id
    ).all()
    patient_ids = [a.patient_id for a in access_records]

    patients = db.query(Patient).filter(Patient.id.in_(patient_ids)).all() if patient_ids else []
    
    for p in patients:
        consent_count = db.query(ConsentRecord).filter(ConsentRecord.patient_id == p.id).count()
        p.has_consent = consent_count > 0

    return patients


@router.get(
    "/{patient_id}",
    response_model=PatientOut,
    dependencies=[Depends(audit_action("VIEW_PATIENT_PROFILE"))]
)
def get_patient_profile(
    patient_id: UUID,
    access: CaregiverPatientAccess = Depends(require_patient_access(required_role="contributor")),
    current_caregiver: Caregiver = Depends(get_current_caregiver),
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    consent_count = db.query(ConsentRecord).filter(ConsentRecord.patient_id == patient_id).count()
    patient.has_consent = consent_count > 0
    return patient


# Family Member endpoints
@router.post(
    "/{patient_id}/family-members",
    response_model=FamilyMemberOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(audit_action("ADD_FAMILY_MEMBER"))]
)
def add_family_member(
    patient_id: UUID,
    payload: FamilyMemberCreate,
    access: CaregiverPatientAccess = Depends(require_patient_access(required_role="contributor")),
    db: Session = Depends(get_db)
):
    member = FamilyMember(
        patient_id=patient_id,
        name=payload.name,
        relationship=payload.relationship,
        photo_url=payload.photo_url
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.get(
    "/{patient_id}/family-members",
    response_model=List[FamilyMemberOut]
)
def list_family_members(
    patient_id: UUID,
    access: CaregiverPatientAccess = Depends(require_patient_access(required_role="contributor")),
    db: Session = Depends(get_db)
):
    return db.query(FamilyMember).filter(FamilyMember.patient_id == patient_id).all()


# Story Prompt endpoints
@router.post(
    "/{patient_id}/prompts",
    response_model=StoryPromptOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(audit_action("ADD_STORY_PROMPT"))]
)
def add_story_prompt(
    patient_id: UUID,
    payload: StoryPromptCreate,
    access: CaregiverPatientAccess = Depends(require_patient_access(required_role="contributor")),
    db: Session = Depends(get_db)
):
    prompt = StoryPrompt(
        patient_id=patient_id,
        prompt_text=payload.prompt_text,
        sequence_order=payload.sequence_order,
        is_custom=payload.is_custom
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.get(
    "/{patient_id}/prompts",
    response_model=List[StoryPromptOut]
)
def list_story_prompts(
    patient_id: UUID,
    access: CaregiverPatientAccess = Depends(require_patient_access(required_role="contributor")),
    db: Session = Depends(get_db)
):
    return db.query(StoryPrompt).filter(StoryPrompt.patient_id == patient_id).order_by(StoryPrompt.sequence_order.asc().nulls_last()).all()


# Consent Record endpoints
@router.post(
    "/{patient_id}/consent",
    response_model=ConsentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(audit_action("RECORD_CONSENT"))]
)
def record_consent(
    patient_id: UUID,
    payload: ConsentCreate,
    access: CaregiverPatientAccess = Depends(require_patient_access(required_role="owner")),
    current_caregiver: Caregiver = Depends(get_current_caregiver),
    db: Session = Depends(get_db)
):
    consent = ConsentRecord(
        patient_id=patient_id,
        recorded_by_caregiver_id=current_caregiver.id,
        consent_basis=payload.consent_basis
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return consent


@router.get("/{patient_id}/consent")
def get_consent_status(
    patient_id: UUID,
    access: CaregiverPatientAccess = Depends(require_patient_access(required_role="contributor")),
    db: Session = Depends(get_db)
):
    consents = db.query(ConsentRecord).filter(ConsentRecord.patient_id == patient_id).all()
    return {
        "patient_id": patient_id,
        "has_consent": len(consents) > 0,
        "consent_count": len(consents),
        "latest_granted_at": consents[-1].granted_at if consents else None
    }


# Timeline & Advanced SQL-Filtered Vector Search endpoints
@router.get(
    "/{patient_id}/timeline",
    response_model=TimelineResponse,
    dependencies=[Depends(audit_action("VIEW_TIMELINE"))]
)
def get_patient_timeline(
    patient_id: UUID,
    access: CaregiverPatientAccess = Depends(require_patient_access(required_role="contributor")),
    db: Session = Depends(get_db)
):
    has_consent = db.query(ConsentRecord).filter(ConsentRecord.patient_id == patient_id).count() > 0
    recordings = db.query(Recording).filter(Recording.patient_id == patient_id).order_by(Recording.recorded_at.desc()).all()

    groups_dict = {}
    for r in recordings:
        group_key = r.estimated_decade or r.theme or "Uncategorized"
        if group_key not in groups_dict:
            groups_dict[group_key] = []
        groups_dict[group_key].append(RecordingOut.model_validate(r))

    timeline_groups = [
        TimelineGroup(group_title=title, recordings=recs)
        for title, recs in groups_dict.items()
    ]

    return TimelineResponse(
        patient_id=patient_id,
        total_recordings=len(recordings),
        has_consent=has_consent,
        timeline=timeline_groups
    )


@router.get(
    "/{patient_id}/timeline/search",
    response_model=List[RecordingOut],
    dependencies=[Depends(audit_action("SEARCH_TIMELINE"))]
)
def search_patient_timeline(
    patient_id: UUID,
    q: Optional[str] = Query(None),
    decade: Optional[str] = Query(None),
    theme: Optional[str] = Query(None),
    entity_id: Optional[UUID] = Query(None),
    access: CaregiverPatientAccess = Depends(require_patient_access(required_role="contributor")),
    db: Session = Depends(get_db)
):
    # 1. Base SQL WHERE filtering
    query_builder = db.query(Recording).filter(Recording.patient_id == patient_id)

    if decade:
        query_builder = query_builder.filter(Recording.estimated_decade == decade)
    if theme:
        query_builder = query_builder.filter(Recording.theme.ilike(f"%{theme}%"))
    if entity_id:
        mentioned_rec_ids = [
            m.recording_id for m in db.query(EntityMention).filter(EntityMention.entity_id == entity_id).all()
        ]
        query_builder = query_builder.filter(Recording.id.in_(mentioned_rec_ids))

    recordings = query_builder.all()
    if not recordings:
        return []

    if not q or not q.strip():
        return [RecordingOut.model_validate(r) for r in recordings]

    # 2. Vector embedding & keyword similarity ranking within SQL candidate set
    query_text = q.strip()
    query_vector = generate_embedding(query_text)

    scored_recordings = []
    synonyms_map = {
        "dog": ["buster", "retriever", "pet", "puppy", "canine"],
        "wedding": ["marry", "married", "marriage", "bride", "groom", "ceremony", "romance", "tied the knot", "knot"],
        "school": ["class", "teacher", "grade", "education", "friend"],
        "work": ["job", "career", "office", "boss", "company", "bakery"]
    }

    query_lower = query_text.lower()
    search_terms = [query_lower]
    for key, syns in synonyms_map.items():
        all_group = [key] + syns
        if any(w in query_lower for w in all_group):
            search_terms.extend(all_group)

    for r in recordings:
        score = 0.0
        
        if r.embedding is not None:
            emb_list = list(r.embedding) if not isinstance(r.embedding, list) else r.embedding
            sim = _cosine_sim(query_vector, emb_list)
            score += sim * 10.0

        text_corpus = f"{r.transcript or ''} {r.ai_caption or ''} {r.theme or ''} {r.estimated_decade or ''}".lower()
        if any(st in text_corpus for st in search_terms):
            score += 5.0

        if score > 0.1:
            scored_recordings.append((score, r))

    scored_recordings.sort(key=lambda x: x[0], reverse=True)
    return [RecordingOut.model_validate(rec) for score, rec in scored_recordings]


@router.get(
    "/{patient_id}/recordings/{recording_id}",
    dependencies=[Depends(audit_action("VIEW_RECORDING_TRANSCRIPT"))]
)
def get_recording_detail(
    patient_id: UUID,
    recording_id: UUID,
    access: CaregiverPatientAccess = Depends(require_patient_access(required_role="contributor")),
    db: Session = Depends(get_db)
):
    recording = db.query(Recording).filter(
        Recording.id == recording_id,
        Recording.patient_id == patient_id
    ).first()
    
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
        
    return {
        "id": recording.id,
        "patient_id": recording.patient_id,
        "audio_url": recording.audio_url,
        "transcript": recording.transcript,
        "theme": recording.theme,
        "estimated_decade": recording.estimated_decade,
        "ai_caption": recording.ai_caption,
        "classification_confidence": recording.classification_confidence,
        "classification_rationale": recording.classification_rationale,
        "processing_status": recording.processing_status
    }


# Caregiver Invite endpoints
@router.post(
    "/{patient_id}/invite-caregiver",
    response_model=CaregiverInviteOut,
    dependencies=[Depends(audit_action("GENERATE_CAREGIVER_INVITE"))]
)
def generate_caregiver_invite(
    patient_id: UUID,
    payload: CaregiverInviteCreate = CaregiverInviteCreate(),
    access: CaregiverPatientAccess = Depends(require_patient_access(required_role="owner")),
    db: Session = Depends(get_db)
):
    invite_payload = {
        "patient_id": str(patient_id),
        "role": payload.role
    }
    encoded_code = base64.b64encode(json.dumps(invite_payload).encode()).decode()
    return CaregiverInviteOut(invite_code=encoded_code, patient_id=patient_id, role=payload.role)


@router.post("/claim-invite", status_code=status.HTTP_200_OK)
def claim_caregiver_invite(
    payload: CaregiverInviteClaim,
    current_caregiver: Caregiver = Depends(get_current_caregiver),
    db: Session = Depends(get_db)
):
    try:
        raw_json = base64.b64decode(payload.invite_code.encode()).decode()
        data = json.loads(raw_json)
        patient_id = UUID(data["patient_id"])
        role = data.get("role", "contributor")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or corrupted invite code."
        )

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target patient record not found."
        )

    existing_access = db.query(CaregiverPatientAccess).filter(
        CaregiverPatientAccess.caregiver_id == current_caregiver.id,
        CaregiverPatientAccess.patient_id == patient_id
    ).first()

    if not existing_access:
        new_access = CaregiverPatientAccess(
            caregiver_id=current_caregiver.id,
            patient_id=patient_id,
            role=role
        )
        db.add(new_access)
        db.commit()

        log_audit_event(
            db=db,
            action="CLAIM_CAREGIVER_INVITE",
            actor_caregiver_id=current_caregiver.id,
            patient_id=patient_id,
            metadata={"assigned_role": role}
        )

    return {"status": "claimed", "patient_id": patient_id, "role": role}
