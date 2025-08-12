from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class InterviewType(str, Enum):
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    CULTURE_FIT = "culture_fit"
    SYSTEM_DESIGN = "system_design"
    PAIR_PROGRAMMING = "pair_programming"
    CASE_STUDY = "case_study"

class InterviewStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"

class Interviewer(BaseModel):
    id: str
    name: str
    email: str
    role: str
    department: str

class Question(BaseModel):
    id: Optional[str] = None
    text: str
    category: str
    difficulty: str
    expected_answer: Optional[str] = None
    evaluation_criteria: List[str]

class InterviewFeedback(BaseModel):
    interviewer_id: str
    technical_score: Optional[float] = None
    communication_score: Optional[float] = None
    problem_solving_score: Optional[float] = None
    culture_fit_score: Optional[float] = None
    strengths: List[str]
    areas_for_improvement: List[str]
    notes: str
    recommendation: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(String(36), primary_key=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id"), nullable=False)
    interview_type = Column(String(50), nullable=False)  # e.g., "technical", "behavioral", "cultural"
    status = Column(String(20), default="scheduled")  # scheduled, completed, cancelled
    scheduled_time = Column(DateTime)
    duration_minutes = Column(String(10))
    location = Column(String(255))  # URL for virtual interviews, physical location for in-person
    participants = Column(Text)  # JSON string of participant IDs
    preferred_times = Column(Text)  # JSON string of preferred time slots
    notes = Column(Text)
    feedback = Column(Text)  # JSON string of interview feedback
    evaluation = Column(Text)  # JSON string of candidate evaluation
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    candidate = relationship("Candidate", backref="interviews")

    @classmethod
    def get_by_id(cls, interview_id: str) -> Optional['Interview']:
        """Get interview by ID."""
        return cls.query.filter_by(id=interview_id).first()

    @classmethod
    def get_by_candidate(cls, candidate_id: str) -> List['Interview']:
        """Get all interviews for a candidate."""
        return cls.query.filter_by(candidate_id=candidate_id).all()

    @classmethod
    def get_upcoming(cls, days: int = 7) -> List['Interview']:
        """Get upcoming interviews within specified days."""
        end_date = datetime.utcnow() + timedelta(days=days)
        return cls.query.filter(
            cls.scheduled_time >= datetime.utcnow(),
            cls.scheduled_time <= end_date,
            cls.status == "scheduled"
        ).all()

    def to_dict(self) -> Dict[str, Any]:
        """Convert interview to dictionary."""
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "interview_type": self.interview_type,
            "status": self.status,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "duration_minutes": self.duration_minutes,
            "location": self.location,
            "participants": self.participants,
            "preferred_times": self.preferred_times,
            "notes": self.notes,
            "feedback": self.feedback,
            "evaluation": self.evaluation,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class InterviewCreate(BaseModel):
    candidate_id: str
    job_posting_id: str
    interview_type: InterviewType
    scheduled_at: datetime
    duration_minutes: int
    interviewers: List[Interviewer]
    questions: List[Question]

class InterviewUpdate(BaseModel):
    interview_type: Optional[InterviewType] = None
    status: Optional[InterviewStatus] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    interviewers: Optional[List[Interviewer]] = None
    questions: Optional[List[Question]] = None
    feedback: Optional[List[InterviewFeedback]] = None
    notes: Optional[str] = None 