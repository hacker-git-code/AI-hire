import google.generativeai as genai
from typing import List, Dict, Any, Optional
from app.core.config import settings

class GeminiService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GeminiService, cls).__new__(cls)
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            cls.model = genai.GenerativeModel('gemini-pro')
        return cls._instance
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Gemini"""
        response = await self.model.generate_content_async(prompt, **kwargs)
        return response.text
    
    async def analyze_resume(
        self, 
        resume_text: str, 
        job_description: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Analyze resume against job description"""
        prompt = f"""
        Analyze the following resume against the job description and provide a detailed analysis.
        
        JOB DESCRIPTION:
        {job_description}
        
        RESUME:
        {resume_text}
        
        Provide analysis in the following format:
        1. Overall match percentage (0-100%)
        2. Key strengths
        3. Potential concerns
        4. Recommended next steps
        5. Suggested interview questions
        """
        
        analysis = await self.generate_text(prompt, **kwargs)
        
        # Parse the response into a structured format
        return {
            "analysis": analysis,
            "metadata": {
                "model": "gemini-pro",
                "timestamp": "2023-01-01T00:00:00Z"  # Add actual timestamp
            }
        }
    
    async def generate_interview_questions(
        self,
        role: str,
        experience_level: str,
        num_questions: int = 5,
        **kwargs
    ) -> List[str]:
        """Generate interview questions for a specific role and experience level"""
        prompt = f"""
        Generate {num_questions} technical interview questions for a {experience_level} {role} position.
        Focus on assessing both technical skills and problem-solving abilities.
        Return each question on a new line.
        """
        
        questions = await self.generate_text(prompt, **kwargs)
        return [q.strip() for q in questions.split('\n') if q.strip()]
