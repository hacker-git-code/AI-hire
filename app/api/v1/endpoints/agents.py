from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from app.agents.specialized import (
    screener_agent,
    interviewer_agent,
    matcher_agent,
    coordinator_agent
)

router = APIRouter()

@router.post("/screener")
async def run_screener(input_text: str):
    """Run the screener agent."""
    try:
        result = screener_agent.run(input_text)
        return {
            "agent": "screener",
            "result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/interviewer")
async def run_interviewer(input_text: str):
    """Run the interviewer agent."""
    try:
        result = interviewer_agent.run(input_text)
        return {
            "agent": "interviewer",
            "result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/matcher")
async def run_matcher(input_text: str):
    """Run the matcher agent."""
    try:
        result = matcher_agent.run(input_text)
        return {
            "agent": "matcher",
            "result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/coordinator")
async def run_coordinator(input_text: str):
    """Run the coordinator agent."""
    try:
        result = coordinator_agent.run(input_text)
        return {
            "agent": "coordinator",
            "result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/status")
async def get_agents_status():
    """Get status of all agents."""
    return {
        "screener": {
            "name": screener_agent.name,
            "role": screener_agent.role,
            "status": "active"
        },
        "interviewer": {
            "name": interviewer_agent.name,
            "role": interviewer_agent.role,
            "status": "active"
        },
        "matcher": {
            "name": matcher_agent.name,
            "role": matcher_agent.role,
            "status": "active"
        },
        "coordinator": {
            "name": coordinator_agent.name,
            "role": coordinator_agent.role,
            "status": "active"
        }
    } 