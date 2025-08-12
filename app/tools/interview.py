from typing import Dict, Any, List
from langchain.tools import BaseTool
from app.services.interview import InterviewService

class InterviewTool(BaseTool):
    name = "interview"
    description = "Conduct interviews and evaluate candidate responses"

    def __init__(self):
        super().__init__()
        self.interview_service = InterviewService()

    def _run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process interview input and return evaluation."""
        try:
            action = input_data.get("action")
            if action == "generate_questions":
                questions = self.interview_service.generate_questions(
                    job_description=input_data.get("job_description"),
                    candidate_profile=input_data.get("candidate_profile")
                )
                return {
                    "status": "success",
                    "questions": questions
                }
            elif action == "evaluate_response":
                evaluation = self.interview_service.evaluate_response(
                    question=input_data.get("question"),
                    response=input_data.get("response"),
                    context=input_data.get("context", {})
                )
                return {
                    "status": "success",
                    "evaluation": evaluation
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
        """Async implementation of interview processing."""
        return self._run(input_data) 