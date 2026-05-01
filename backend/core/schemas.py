"""Pydantic models shared across routers."""
from typing import List, Optional
from pydantic import BaseModel, EmailStr


# ---- Users / Auth ----
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    id: str
    email: str
    full_name: str
    plan: str = "free"
    credits: int = 100
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: UserPublic


# ---- Projects ----
class ProjectCreate(BaseModel):
    topic: str
    audience: str = "general"
    duration_seconds: int = 60
    tone: str = "engaging"
    language: str = "English"
    style: str = "storytelling"
    niche: str = "general"


class Project(BaseModel):
    id: str
    user_id: str
    topic: str
    audience: str
    duration_seconds: int
    tone: str
    language: str
    style: str
    niche: str
    status: str
    title: Optional[str] = None
    description: Optional[str] = None
    script: Optional[dict] = None
    voice: Optional[dict] = None
    thumbnail_url: Optional[str] = None
    thumbnail_path: Optional[str] = None
    scene_images: Optional[List[dict]] = None
    scenes_status: Optional[str] = None
    video_path: Optional[str] = None
    video_url: Optional[str] = None
    youtube_video_id: Optional[str] = None
    youtube_url: Optional[str] = None
    uploaded_real: Optional[bool] = None
    scheduled_at: Optional[str] = None
    script_variants: Optional[List[dict]] = None
    selected_variant_id: Optional[str] = None
    template_id: Optional[str] = None
    ab_winner: Optional[str] = None
    ab_metrics: Optional[dict] = None
    created_at: str
    updated_at: str


# ---- Pipeline payloads ----
class ScriptGenerateRequest(BaseModel):
    project_id: str
    style: Optional[str] = None
    variant: Optional[str] = "default"


class VoiceGenerateRequest(BaseModel):
    project_id: str
    voice: str = "alloy"
    speed: float = 1.0


class ThumbnailGenerateRequest(BaseModel):
    project_id: str
    style_prompt: Optional[str] = None


class PublishRequest(BaseModel):
    project_id: str
    title: str
    description: str
    tags: List[str] = []
    privacy: str = "public"
    schedule_at: Optional[str] = None


class ScenesGenerateRequest(BaseModel):
    project_id: str


class RenderRequest(BaseModel):
    project_id: str


# ---- Series ----
class SeriesRequest(BaseModel):
    niche: str
    base_topic: str
    count: int = 5
    duration_seconds: int = 60
    audience: str = "general"
    tone: str = "engaging"
    language: str = "English"
    style: str = "storytelling"


# ---- Templates ----
class CreateFromTemplateRequest(BaseModel):
    template_id: str
    topic: Optional[str] = None


# ---- A/B variants ----
class VariantGenerateRequest(BaseModel):
    project_id: str
    style_a: str = "storytelling"
    style_b: str = "listicle"


class SelectVariantRequest(BaseModel):
    project_id: str
    variant_id: str  # 'A' or 'B'


class VariantScoreRequest(BaseModel):
    project_id: str
    variant_id: str  # 'A' or 'B'
    hook_score: float = 0.0  # 0-10
    title_score: float = 0.0
    overall_score: float = 0.0
    note: Optional[str] = None


# ---- Billing ----
class CheckoutRequest(BaseModel):
    plan_id: str
    origin_url: str


# ---- Agent ----
class AgentRunRequest(BaseModel):
    topic: str
    niche: str = "general"
    duration_seconds: int = 60
    tone: str = "engaging"
    style: str = "storytelling"
    language: str = "English"
    audience: str = "general"
    voice: str = "alloy"
    auto_publish: bool = False
    youtube_privacy: str = "private"
