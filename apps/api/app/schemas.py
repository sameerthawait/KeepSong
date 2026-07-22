from datetime import datetime
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# Caregiver Auth Schemas
class CaregiverRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str

class CaregiverLogin(BaseModel):
    email: EmailStr
    password: str

class CaregiverOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    name: str
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

TokenRefresh = RefreshTokenRequest

# Patient Auth Schemas
class PatientPinVerify(BaseModel):
    patient_id: UUID
    pin: str = Field(min_length=4, max_length=6)

class PatientTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    patient_id: UUID
    patient_name: str

# Patient Management Schemas
class PatientCreate(BaseModel):
    name: str
    pin: Optional[str] = Field(default="1234", min_length=4, max_length=6)

class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    primary_caregiver_id: Optional[UUID] = None
    created_at: datetime
    has_consent: bool = False

# Family Member Schemas
class FamilyMemberCreate(BaseModel):
    name: str
    relationship: str
    photo_url: Optional[str] = None

class FamilyMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    name: str
    relationship: str
    photo_url: Optional[str] = None
    created_at: datetime

# Story Prompt Schemas
class StoryPromptCreate(BaseModel):
    prompt_text: str
    sequence_order: Optional[int] = None
    is_custom: bool = True

class StoryPromptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    prompt_text: str
    sequence_order: Optional[int] = None
    is_custom: bool
    created_at: datetime

# Consent Record Schemas
class ConsentCreate(BaseModel):
    consent_basis: str = Field(default="Signed proxy consent form")

class ConsentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    recorded_by_caregiver_id: Optional[UUID] = None
    consent_basis: str
    granted_at: datetime

# Object Storage Presigned Upload Schemas
class UploadUrlRequest(BaseModel):
    content_type: str
    file_size: int
    category: str = Field(default="audio")
    filename: Optional[str] = None

class UploadUrlResponse(BaseModel):
    upload_url: str
    asset_url: str
    file_key: str
    expires_in: int = 900

# Recording Schemas
class RecordingCreate(BaseModel):
    audio_url: str
    prompt_id: Optional[UUID] = None
    duration_seconds: Optional[int] = None

class RecordingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    prompt_id: Optional[UUID] = None
    audio_url: str
    transcript: Optional[str] = None
    theme: Optional[str] = None
    estimated_decade: Optional[str] = None
    ai_caption: Optional[str] = None
    classification_confidence: Optional[float] = None
    classification_rationale: Optional[str] = None
    model_identifier: Optional[str] = None
    prompt_version: Optional[str] = None
    duration_seconds: Optional[int] = None
    processing_status: str
    failure_stage: Optional[str] = None
    recorded_at: datetime

# Timeline Response Schemas
class TimelineGroup(BaseModel):
    group_title: str
    recordings: List[RecordingOut]

class TimelineResponse(BaseModel):
    patient_id: UUID
    total_recordings: int
    has_consent: bool
    timeline: List[TimelineGroup]

# Caregiver Invite Schemas
class CaregiverInviteCreate(BaseModel):
    role: str = Field(default="contributor")

class CaregiverInviteOut(BaseModel):
    invite_code: str
    patient_id: UUID
    role: str

class CaregiverInviteClaim(BaseModel):
    invite_code: str

# Phase 8 Knowledge Graph Schemas
class EntityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    type: str
    name: str
    first_mentioned_recording_id: Optional[UUID] = None

class EntityMentionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entity_id: UUID
    recording_id: UUID
    confidence: float
    model_identifier: Optional[str] = None
    prompt_version: Optional[str] = None
    created_at: datetime

class RelationshipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entity_id_a: UUID
    entity_id_b: UUID
    relationship_type: str

class GraphResponse(BaseModel):
    entities: List[EntityOut]
    relationships: List[RelationshipOut]

class SuggestedPromptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    entity_id: Optional[UUID] = None
    prompt_text: str
    is_approved: bool
    created_at: datetime

class PhotoCaptionSuggestRequest(BaseModel):
    photo_url: str
    family_member_name: Optional[str] = None
    relationship: Optional[str] = None

class PhotoCaptionSuggestResponse(BaseModel):
    suggested_caption: str
    label: str = "AI suggestion — please review"
