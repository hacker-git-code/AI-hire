from typing import Dict, Any, List
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.core.config import settings

class ResumeParserService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.3,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert resume parser. Extract and structure the following information from the resume:
            1. Personal Information
            2. Work Experience
            3. Education
            4. Skills
            5. Projects
            6. Certifications
            7. Languages
            8. Summary/Objective
            
            For each section, provide detailed analysis and validation."""),
            ("human", "{resume_text}")
        ])

    def parse(self, resume_text: str) -> Dict[str, Any]:
        """Parse resume text and return structured information."""
        try:
            # Format the prompt with the resume text
            formatted_prompt = self.prompt.format_messages(resume_text=resume_text)
            
            # Get the LLM response
            response = self.llm(formatted_prompt)
            
            # Process and structure the response
            parsed_data = self._process_response(response.content)
            
            return parsed_data
        except Exception as e:
            raise Exception(f"Error parsing resume: {str(e)}")

    def _process_response(self, response: str) -> Dict[str, Any]:
        """Process the LLM response into structured data."""
        # Here you would implement the logic to parse the LLM response
        # into a structured format. This is a simplified example.
        sections = response.split("\n\n")
        structured_data = {}
        
        for section in sections:
            if ":" in section:
                key, value = section.split(":", 1)
                structured_data[key.strip()] = value.strip()
        
        return structured_data

    def validate(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the parsed resume data."""
        validation_results = {
            "is_valid": True,
            "issues": []
        }
        
        # Check for required sections
        required_sections = ["Personal Information", "Work Experience", "Education", "Skills"]
        for section in required_sections:
            if section not in parsed_data:
                validation_results["is_valid"] = False
                validation_results["issues"].append(f"Missing required section: {section}")
        
        # Validate work experience dates
        if "Work Experience" in parsed_data:
            # Add date validation logic here
            pass
        
        # Validate education dates
        if "Education" in parsed_data:
            # Add date validation logic here
            pass
        
        return validation_results 