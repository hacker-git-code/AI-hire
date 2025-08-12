from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import Column, String, DateTime, Enum, Text
from app.core.database import Base
from app.models.pipeline import PipelineStage

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String(36), primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20))
    resume_url = Column(String(255))
    linkedin_url = Column(String(255))
    github_url = Column(String(255))
    portfolio_url = Column(String(255))
    
    # Professional Information
    current_title = Column(String(100))
    current_company = Column(String(100))
    years_of_experience = Column(String(20))
    skills = Column(Text)  # JSON string of skills
    education = Column(Text)  # JSON string of education history
    work_experience = Column(Text)  # JSON string of work experience
    
    # Pipeline Information
    pipeline_stage = Column(Enum(PipelineStage), default=PipelineStage.SCREENING)
    pipeline_notes = Column(Text)
    assigned_recruiter = Column(String(36))  # User ID of assigned recruiter
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_by_id(cls, candidate_id: str) -> Optional['Candidate']:
        """Get candidate by ID."""
        return cls.query.filter_by(id=candidate_id).first()

    @classmethod
    def get_by_email(cls, email: str) -> Optional['Candidate']:
        """Get candidate by email."""
        return cls.query.filter_by(email=email).first()

    @classmethod
    def get_by_date_range(cls, start_date: datetime, end_date: datetime) -> List['Candidate']:
        """Get candidates created within date range."""
        return cls.query.filter(
            cls.created_at >= start_date,
            cls.created_at <= end_date
        ).all()

    def to_dict(self) -> Dict[str, Any]:
        """Convert candidate to dictionary."""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "resume_url": self.resume_url,
            "linkedin_url": self.linkedin_url,
            "github_url": self.github_url,
            "portfolio_url": self.portfolio_url,
            "current_title": self.current_title,
            "current_company": self.current_company,
            "years_of_experience": self.years_of_experience,
            "skills": self.skills,
            "education": self.education,
            "work_experience": self.work_experience,
            "pipeline_stage": self.pipeline_stage.value if self.pipeline_stage else None,
            "pipeline_notes": self.pipeline_notes,
            "assigned_recruiter": self.assigned_recruiter,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 