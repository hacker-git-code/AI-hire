from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
from app.models.candidate import CandidateStatus
from app.models.job import JobType, ExperienceLevel, JobStatus
from app.models.interview import InterviewType, InterviewStatus

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    portfolio_url = Column(String, nullable=True)
    resume_url = Column(String, nullable=True)
    current_position = Column(String, nullable=True)
    years_experience = Column(Float)
    skills = Column(JSON)
    experience = Column(JSON)
    education = Column(JSON)
    status = Column(SQLEnum(CandidateStatus), default=CandidateStatus.NEW)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    interviews = relationship("Interview", back_populates="candidate")

class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    company = Column(String)
    description = Column(String)
    requirements = Column(JSON)
    responsibilities = Column(JSON)
    job_type = Column(SQLEnum(JobType))
    experience_level = Column(SQLEnum(ExperienceLevel))
    required_skills = Column(JSON)
    location = Column(JSON)
    salary_range = Column(JSON, nullable=True)
    benefits = Column(JSON)
    status = Column(SQLEnum(JobStatus), default=JobStatus.DRAFT)
    closing_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    interviews = relationship("Interview", back_populates="job_posting")

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"))
    interview_type = Column(SQLEnum(InterviewType))
    status = Column(SQLEnum(InterviewStatus), default=InterviewStatus.SCHEDULED)
    scheduled_at = Column(DateTime)
    duration_minutes = Column(Integer)
    interviewers = Column(JSON)
    questions = Column(JSON)
    feedback = Column(JSON, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="interviews")
    job_posting = relationship("JobPosting", back_populates="interviews") 