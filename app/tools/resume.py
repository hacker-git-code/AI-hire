from typing import Dict, Any
from langchain.tools import BaseTool
from app.services.resume_parser import ResumeParserService

class ResumeParserTool(BaseTool):
    name = "resume_parser"
    description = "Parse and analyze resume content to extract candidate information"

    def __init__(self):
        super().__init__()
        self.parser_service = ResumeParserService()

    def _run(self, resume_text: str) -> Dict[str, Any]:
        """Parse resume text and return structured information."""
        try:
            result = self.parser_service.parse(resume_text)
            return {
                "status": "success",
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def _arun(self, resume_text: str) -> Dict[str, Any]:
        """Async implementation of resume parsing."""
        return self._run(resume_text) 