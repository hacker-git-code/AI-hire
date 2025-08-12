from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.candidate import Candidate
from app.agents.specialized import screener_agent
from app.services.resume_parser import ResumeParserService

router = APIRouter()
resume_parser = ResumeParserService()

@router.post("/")
async def create_candidate(
    first_name: str,
    last_name: str,
    email: str,
    phone: Optional[str] = None,
    resume: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Create a new candidate."""
    try:
        # Check if candidate already exists
        existing_candidate = Candidate.get_by_email(email)
        if existing_candidate:
            raise HTTPException(
                status_code=400,
                detail="Candidate with this email already exists"
            )
        
        # Parse resume
        resume_content = await resume.read()
        parsed_data = resume_parser.parse(resume_content.decode())
        
        # Create candidate
        candidate = Candidate(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            resume_url=resume.filename,  # In production, upload to storage
            **parsed_data
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        
        # Run initial screening
        screening_result = screener_agent.run(
            f"Screen candidate {candidate.id} with the following profile: {candidate.to_dict()}"
        )
        
        return {
            "candidate": candidate.to_dict(),
            "screening_result": screening_result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/{candidate_id}")
async def get_candidate(
    candidate_id: str,
    db: Session = Depends(get_db)
):
    """Get candidate by ID."""
    candidate = Candidate.get_by_id(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )
    return candidate.to_dict()

@router.get("/")
async def list_candidates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all candidates."""
    candidates = db.query(Candidate).offset(skip).limit(limit).all()
    return [candidate.to_dict() for candidate in candidates]

@router.put("/{candidate_id}")
async def update_candidate(
    candidate_id: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update candidate information."""
    candidate = Candidate.get_by_id(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )
    
    # Update fields if provided
    if first_name:
        candidate.first_name = first_name
    if last_name:
        candidate.last_name = last_name
    if email:
        candidate.email = email
    if phone:
        candidate.phone = phone
    
    db.commit()
    db.refresh(candidate)
    return candidate.to_dict()

@router.delete("/{candidate_id}")
async def delete_candidate(
    candidate_id: str,
    db: Session = Depends(get_db)
):
    """Delete a candidate."""
    candidate = Candidate.get_by_id(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )
    
    db.delete(candidate)
    db.commit()
    return {"message": "Candidate deleted successfully"} 