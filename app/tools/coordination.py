from typing import Dict, Any, List
from langchain.tools import BaseTool
from app.services.coordination import CoordinationService

class CoordinationTool(BaseTool):
    name = "coordination"
    description = "Manage hiring workflow and coordinate between agents"

    def __init__(self):
        super().__init__()
        self.coordination_service = CoordinationService()

    def _run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process coordination input and return workflow status."""
        try:
            action = input_data.get("action")
            if action == "update_pipeline":
                status = self.coordination_service.update_pipeline(
                    candidate_id=input_data.get("candidate_id"),
                    stage=input_data.get("stage"),
                    notes=input_data.get("notes", "")
                )
                return {
                    "status": "success",
                    "pipeline_status": status
                }
            elif action == "schedule_interview":
                schedule = self.coordination_service.schedule_interview(
                    candidate_id=input_data.get("candidate_id"),
                    interview_type=input_data.get("interview_type"),
                    participants=input_data.get("participants", []),
                    preferred_times=input_data.get("preferred_times", [])
                )
                return {
                    "status": "success",
                    "schedule": schedule
                }
            elif action == "get_process_insights":
                insights = self.coordination_service.get_process_insights(
                    time_period=input_data.get("time_period"),
                    metrics=input_data.get("metrics", [])
                )
                return {
                    "status": "success",
                    "insights": insights
                }
            else:
                return {
                    "status": "error",
                    "error": "Invalid action specified"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def _arun(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Async implementation of coordination processing."""
        return self._run(input_data) 