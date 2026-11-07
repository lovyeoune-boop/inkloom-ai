from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional

AgeBand = Literal["under_5", "5_8", "9_12", "13_17"]
ContentType = Literal["text", "image", "audio", "video"]

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class ProfileUpdateIn(BaseModel):
    email: EmailStr

class PasswordChangeIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ReviewTextIn(BaseModel):
    title: str = Field(min_length=1, max_length=250)
    content: str = Field(min_length=1, max_length=50000)
    age_band: AgeBand

class ReviewDecisionIn(BaseModel):
    action: Literal["approve", "request_changes", "escalate"]
    note: str = Field(default="", max_length=5000)

class Finding(BaseModel):
    category: str
    severity: Literal["low", "medium", "high", "critical"]
    explanation: str
    evidence: Optional[str] = None
    recommendation: str

class ModerationResult(BaseModel):
    recommendation: Literal["age_appropriate", "not_recommended", "review_required"]
    risk_level: Literal["low", "medium", "high", "critical", "unknown"]
    findings: list[Finding]
    human_review_required: bool = True
