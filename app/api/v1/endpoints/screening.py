from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from app.services.ai_screening import AIScreeningService
from app.models.candidate import Candidate
from app.models.job import JobPosting
import json

router = APIRouter()
screening_service = AIScreeningService()

@router.post("/evaluate")
async def evaluate_candidate(
    candidate: Candidate,
    job: JobPosting
) -> Dict[str, Any]:
    """
    Evaluate a candidate's fit for a specific job posting.
    """
    try:
        evaluation = await screening_service.evaluate_candidate(candidate, job)
        return evaluation
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating candidate: {str(e)}"
        )

@router.post("/generate-questions")
async def generate_interview_questions(
    candidate: Candidate,
    job: JobPosting
) -> List[Dict[str, Any]]:
    """
    Generate tailored interview questions based on candidate profile and job requirements.
    """
    try:
        questions = await screening_service.generate_interview_questions(candidate, job)
        return questions
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating questions: {str(e)}"
        )

@router.post("/analyze-resume")
async def analyze_resume(
    resume: UploadFile = File(...)
) -> Dict[str, Any]:
    """
    Analyze a resume and extract structured information.
    """
    try:
        # Read resume content
        content = await resume.read()
        resume_text = content.decode("utf-8")
        
        # Analyze resume
        analysis = await screening_service.analyze_resume(resume_text)
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing resume: {str(e)}"
        )

@router.post("/match-candidates")
async def match_candidates(
    job: JobPosting,
    candidates: List[Candidate]
) -> List[Dict[str, Any]]:
    """
    Match multiple candidates against a job posting and rank them.
    """
    try:
        results = []
        for candidate in candidates:
            evaluation = await screening_service.evaluate_candidate(candidate, job)
            results.append({
                "candidate_id": candidate.id,
                "evaluation": evaluation
            })
        
        # Sort results by overall match score
        results.sort(key=lambda x: x["evaluation"].get("overall_score", 0), reverse=True)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error matching candidates: {str(e)}"
        ) 