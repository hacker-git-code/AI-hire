from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.interview import Interview
from app.models.candidate import Candidate
from app.agents.specialized import interviewer_agent
from app.services.interview import InterviewService

router = APIRouter()
interview_service = InterviewService()

@router.post("/")
async def create_interview(
    candidate_id: str,
    interview_type: str,
    participants: List[str],
    preferred_times: List[datetime],
    db: Session = Depends(get_db)
):
    """Create a new interview."""
    try:
        # Check if candidate exists
        candidate = Candidate.get_by_id(candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=404,
                detail="Candidate not found"
            )
        
        # Generate interview questions
        questions = interview_service.generate_questions(
            job_description="",  # In production, get from job posting
            candidate_profile=candidate.to_dict()
        )
        
        # Create interview
        interview = Interview(
            candidate_id=candidate_id,
            interview_type=interview_type,
            participants=participants,
            preferred_times=preferred_times,
            status="scheduled"
        )
        db.add(interview)
        db.commit()
        db.refresh(interview)
        
        return {
            "interview": interview.to_dict(),
            "questions": questions
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/{interview_id}")
async def get_interview(
    interview_id: str,
    db: Session = Depends(get_db)
):
    """Get interview by ID."""
    interview = Interview.get_by_id(interview_id)
    if not interview:
        raise HTTPException(
            status_code=404,
            detail="Interview not found"
        )
    return interview.to_dict()

@router.get("/candidate/{candidate_id}")
async def get_candidate_interviews(
    candidate_id: str,
    db: Session = Depends(get_db)
):
    """Get all interviews for a candidate."""
    interviews = Interview.get_by_candidate(candidate_id)
    return [interview.to_dict() for interview in interviews]

@router.post("/{interview_id}/evaluate")
async def evaluate_interview(
    interview_id: str,
    question: str,
    response: str,
    context: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """Evaluate a candidate's response to an interview question."""
    try:
        # Get interview
        interview = Interview.get_by_id(interview_id)
        if not interview:
            raise HTTPException(
                status_code=404,
                detail="Interview not found"
            )
        
        # Evaluate response
        evaluation = interview_service.evaluate_response(
            question=question,
            response=response,
            context=context or {}
        )
        
        # Update interview with evaluation
        if not interview.evaluation:
            interview.evaluation = {}
        interview.evaluation[question] = evaluation
        db.commit()
        
        return evaluation
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.put("/{interview_id}")
async def update_interview(
    interview_id: str,
    status: Optional[str] = None,
    scheduled_time: Optional[datetime] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update interview information."""
    interview = Interview.get_by_id(interview_id)
    if not interview:
        raise HTTPException(
            status_code=404,
            detail="Interview not found"
        )
    
    # Update fields if provided
    if status:
        interview.status = status
    if scheduled_time:
        interview.scheduled_time = scheduled_time
    if notes:
        interview.notes = notes
    
    db.commit()
    db.refresh(interview)
    return interview.to_dict()

@router.delete("/{interview_id}")
async def delete_interview(
    interview_id: str,
    db: Session = Depends(get_db)
):
    """Delete an interview."""
    interview = Interview.get_by_id(interview_id)
    if not interview:
        raise HTTPException(
            status_code=404,
            detail="Interview not found"
        )
    
    db.delete(interview)
    db.commit()
    return {"message": "Interview deleted successfully"} 