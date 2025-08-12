from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class JobType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"

class ExperienceLevel(str, Enum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"

class JobStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"
    FILLED = "filled"

class RequiredSkill(BaseModel):
    name: str
    level: str
    required_years: Optional[float] = None
    is_mandatory: bool = True

class JobLocation(BaseModel):
    city: str
    state: Optional[str] = None
    country: str
    is_remote: bool = False
    remote_allowed: bool = False

class JobPosting(BaseModel):
    id: Optional[str] = None
    title: str
    company: str
    description: str
    requirements: List[str]
    responsibilities: List[str]
    job_type: JobType
    experience_level: ExperienceLevel
    required_skills: List[RequiredSkill]
    location: JobLocation
    salary_range: Optional[dict] = None
    benefits: List[str] = []
    status: JobStatus = JobStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    closing_date: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class JobPostingCreate(BaseModel):
    title: str
    company: str
    description: str
    requirements: List[str]
    responsibilities: List[str]
    job_type: JobType
    experience_level: ExperienceLevel
    required_skills: List[RequiredSkill]
    location: JobLocation
    salary_range: Optional[dict] = None
    benefits: List[str] = []
    closing_date: Optional[datetime] = None

class JobPostingUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    responsibilities: Optional[List[str]] = None
    job_type: Optional[JobType] = None
    experience_level: Optional[ExperienceLevel] = None
    required_skills: Optional[List[RequiredSkill]] = None
    location: Optional[JobLocation] = None
    salary_range: Optional[dict] = None
    benefits: Optional[List[str]] = None
    status: Optional[JobStatus] = None
    closing_date: Optional[datetime] = None 