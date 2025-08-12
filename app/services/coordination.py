from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.core.config import settings
from app.models.candidate import Candidate
from app.models.interview import Interview
from app.models.pipeline import PipelineStage

class CoordinationService:
    def __init__(self):
        self.pipeline_stages = {
            "screening": PipelineStage.SCREENING,
            "interview": PipelineStage.INTERVIEW,
            "assessment": PipelineStage.ASSESSMENT,
            "offer": PipelineStage.OFFER,
            "hired": PipelineStage.HIRED
        }

    def update_pipeline(
        self,
        candidate_id: str,
        stage: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Update candidate's pipeline stage."""
        try:
            # Get candidate
            candidate = Candidate.get_by_id(candidate_id)
            if not candidate:
                raise Exception(f"Candidate not found: {candidate_id}")
            
            # Update stage
            if stage not in self.pipeline_stages:
                raise Exception(f"Invalid pipeline stage: {stage}")
            
            candidate.pipeline_stage = self.pipeline_stages[stage]
            candidate.pipeline_notes = notes
            candidate.updated_at = datetime.utcnow()
            candidate.save()
            
            return {
                "status": "success",
                "candidate_id": candidate_id,
                "stage": stage,
                "updated_at": candidate.updated_at
            }
        except Exception as e:
            raise Exception(f"Error updating pipeline: {str(e)}")

    def schedule_interview(
        self,
        candidate_id: str,
        interview_type: str,
        participants: List[str],
        preferred_times: List[datetime]
    ) -> Dict[str, Any]:
        """Schedule an interview for a candidate."""
        try:
            # Get candidate
            candidate = Candidate.get_by_id(candidate_id)
            if not candidate:
                raise Exception(f"Candidate not found: {candidate_id}")
            
            # Create interview
            interview = Interview(
                candidate_id=candidate_id,
                interview_type=interview_type,
                participants=participants,
                preferred_times=preferred_times,
                status="scheduled"
            )
            interview.save()
            
            # Update candidate pipeline
            self.update_pipeline(
                candidate_id=candidate_id,
                stage="interview",
                notes=f"Scheduled {interview_type} interview"
            )
            
            return {
                "status": "success",
                "interview_id": interview.id,
                "candidate_id": candidate_id,
                "scheduled_time": interview.scheduled_time
            }
        except Exception as e:
            raise Exception(f"Error scheduling interview: {str(e)}")

    def get_process_insights(
        self,
        time_period: str,
        metrics: List[str]
    ) -> Dict[str, Any]:
        """Get insights about the hiring process."""
        try:
            # Calculate time range
            end_date = datetime.utcnow()
            if time_period == "week":
                start_date = end_date - timedelta(days=7)
            elif time_period == "month":
                start_date = end_date - timedelta(days=30)
            elif time_period == "quarter":
                start_date = end_date - timedelta(days=90)
            else:
                raise Exception(f"Invalid time period: {time_period}")
            
            # Get candidates in time range
            candidates = Candidate.get_by_date_range(start_date, end_date)
            
            # Calculate metrics
            insights = {
                "time_period": time_period,
                "total_candidates": len(candidates),
                "metrics": {}
            }
            
            for metric in metrics:
                if metric == "time_to_hire":
                    insights["metrics"]["time_to_hire"] = self._calculate_time_to_hire(candidates)
                elif metric == "stage_distribution":
                    insights["metrics"]["stage_distribution"] = self._calculate_stage_distribution(candidates)
                elif metric == "interview_success_rate":
                    insights["metrics"]["interview_success_rate"] = self._calculate_interview_success_rate(candidates)
                else:
                    raise Exception(f"Invalid metric: {metric}")
            
            return insights
        except Exception as e:
            raise Exception(f"Error getting process insights: {str(e)}")

    def _calculate_time_to_hire(self, candidates: List[Candidate]) -> Dict[str, Any]:
        """Calculate average time to hire."""
        hired_candidates = [c for c in candidates if c.pipeline_stage == PipelineStage.HIRED]
        if not hired_candidates:
            return {"average_days": 0, "min_days": 0, "max_days": 0}
        
        times = []
        for candidate in hired_candidates:
            time_to_hire = (candidate.updated_at - candidate.created_at).days
            times.append(time_to_hire)
        
        return {
            "average_days": sum(times) / len(times),
            "min_days": min(times),
            "max_days": max(times)
        }

    def _calculate_stage_distribution(self, candidates: List[Candidate]) -> Dict[str, int]:
        """Calculate distribution of candidates across pipeline stages."""
        distribution = {stage.value: 0 for stage in PipelineStage}
        for candidate in candidates:
            distribution[candidate.pipeline_stage.value] += 1
        return distribution

    def _calculate_interview_success_rate(self, candidates: List[Candidate]) -> Dict[str, Any]:
        """Calculate interview success rate."""
        interviewed_candidates = [c for c in candidates if c.pipeline_stage in [
            PipelineStage.ASSESSMENT,
            PipelineStage.OFFER,
            PipelineStage.HIRED
        ]]
        if not interviewed_candidates:
            return {"success_rate": 0.0, "total_interviews": 0}
        
        successful_interviews = len(interviewed_candidates)
        total_interviews = len([c for c in candidates if c.pipeline_stage == PipelineStage.INTERVIEW])
        
        return {
            "success_rate": (successful_interviews / total_interviews) * 100 if total_interviews > 0 else 0.0,
            "total_interviews": total_interviews
        } 