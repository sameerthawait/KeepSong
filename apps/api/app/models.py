import uuid
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    Float,
    ForeignKey,
    DateTime,
    Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db import Base
from app.core.security import get_password_hash

class Caregiver(Base):
    __tablename__ = "caregivers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    name = Column(String, nullable=False)
    pin_hash = Column(String, nullable=False, default=lambda: get_password_hash("1234"))
    primary_caregiver_id = Column(UUID(as_uuid=True), ForeignKey("caregivers.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CaregiverPatientAccess(Base):
    __tablename__ = "caregiver_patient_access"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    caregiver_id = Column(UUID(as_uuid=True), ForeignKey("caregivers.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False, default="contributor")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    recorded_by_caregiver_id = Column(UUID(as_uuid=True), ForeignKey("caregivers.id", ondelete="SET NULL"), nullable=True)
    consent_basis = Column(String, nullable=False)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())

class FamilyMember(Base):
    __tablename__ = "family_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    relationship = Column(String, nullable=False)
    photo_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class StoryPrompt(Base):
    __tablename__ = "story_prompts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    prompt_text = Column(String, nullable=False)
    sequence_order = Column(Integer, nullable=True)
    is_custom = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Recording(Base):
    __tablename__ = "recordings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("story_prompts.id", ondelete="SET NULL"), nullable=True)
    audio_url = Column(String, nullable=False)
    transcript = Column(String, nullable=True)
    theme = Column(String, nullable=True)
    estimated_decade = Column(String, nullable=True)
    ai_caption = Column(String, nullable=True)
    classification_confidence = Column(Float, nullable=True)
    classification_rationale = Column(String, nullable=True)
    model_identifier = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    processing_status = Column(String, nullable=False, default="pending")
    failure_stage = Column(String, nullable=True)
    embedding = Column(Vector(1536), nullable=True)

    __table_args__ = (
        Index(
            "ix_recordings_embedding",
            embedding,
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"}
        ),
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    actor_caregiver_id = Column(UUID(as_uuid=True), ForeignKey("caregivers.id", ondelete="SET NULL"), nullable=True)
    patient_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String, nullable=False)
    action_metadata = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Entity(Base):
    __tablename__ = "entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    first_mentioned_recording_id = Column(UUID(as_uuid=True), ForeignKey("recordings.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EntityMention(Base):
    __tablename__ = "entity_mentions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    recording_id = Column(UUID(as_uuid=True), ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False, index=True)
    confidence = Column(Float, nullable=False, default=0.90)
    model_identifier = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EntityRelationship(Base):
    __tablename__ = "entity_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    entity_id_a = Column(UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    entity_id_b = Column(UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String, nullable=False)
    source_recording_id = Column(UUID(as_uuid=True), ForeignKey("recordings.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SuggestedPrompt(Base):
    __tablename__ = "suggested_prompts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    prompt_text = Column(String, nullable=False)
    is_approved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AICallLog(Base):
    __tablename__ = "ai_call_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    patient_id = Column(UUID(as_uuid=True), nullable=True)
    recording_id = Column(UUID(as_uuid=True), nullable=True)
    call_type = Column(String, nullable=False, index=True)
    prompt_version = Column(String, nullable=False, default="v1.0")
    latency_ms = Column(Float, nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    status = Column(String, nullable=False, default="success")
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
