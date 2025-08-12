from typing import Dict, Any, List
from langchain.tools import BaseTool
from app.services.matching import MatchingService

class MatchingTool(BaseTool):
    name = "matching"
    description = "Analyze candidate fit for roles and teams"

    def __init__(self):
        super().__init__()
        self.matching_service = MatchingService()

    def _run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process matching input and return analysis."""
        try:
            action = input_data.get("action")
            if action == "analyze_cultural_fit":
                analysis = self.matching_service.analyze_cultural_fit(
                    candidate_profile=input_data.get("candidate_profile"),
                    team_profile=input_data.get("team_profile")
                )
                return {
                    "status": "success",
                    "analysis": analysis
                }
            elif action == "analyze_skill_fit":
                analysis = self.matching_service.analyze_skill_fit(
                    candidate_skills=input_data.get("candidate_skills"),
                    required_skills=input_data.get("required_skills")
                )
                return {
                    "status": "success",
                    "analysis": analysis
                }
            elif action == "predict_performance":
                prediction = self.matching_service.predict_performance(
                    candidate_profile=input_data.get("candidate_profile"),
                    role_requirements=input_data.get("role_requirements")
                )
                return {
                    "status": "success",
                    "prediction": prediction
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
        """Async implementation of matching analysis."""
        return self._run(input_data) 