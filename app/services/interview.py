from typing import Dict, Any, List
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.core.config import settings

class InterviewService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.question_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert interviewer. Generate relevant interview questions based on the job description and candidate profile.
            Consider:
            1. Technical skills and experience
            2. Problem-solving abilities
            3. Communication skills
            4. Cultural fit
            5. Leadership potential
            
            Generate questions that are:
            - Specific and targeted
            - Open-ended
            - Progressive in difficulty
            - Relevant to the role"""),
            ("human", "Job Description: {job_description}\nCandidate Profile: {candidate_profile}")
        ])
        
        self.evaluation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert interviewer evaluating a candidate's response.
            Consider:
            1. Technical accuracy
            2. Problem-solving approach
            3. Communication clarity
            4. Depth of understanding
            5. Areas for improvement
            
            Provide a detailed evaluation with specific examples."""),
            ("human", "Question: {question}\nResponse: {response}\nContext: {context}")
        ])

    def generate_questions(
        self,
        job_description: str,
        candidate_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate interview questions based on job description and candidate profile."""
        try:
            # Format the prompt
            formatted_prompt = self.question_prompt.format_messages(
                job_description=job_description,
                candidate_profile=str(candidate_profile)
            )
            
            # Get the LLM response
            response = self.llm(formatted_prompt)
            
            # Process and structure the questions
            questions = self._process_questions(response.content)
            
            return questions
        except Exception as e:
            raise Exception(f"Error generating questions: {str(e)}")

    def evaluate_response(
        self,
        question: str,
        response: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a candidate's response to an interview question."""
        try:
            # Format the prompt
            formatted_prompt = self.evaluation_prompt.format_messages(
                question=question,
                response=response,
                context=str(context)
            )
            
            # Get the LLM response
            evaluation = self.llm(formatted_prompt)
            
            # Process and structure the evaluation
            structured_evaluation = self._process_evaluation(evaluation.content)
            
            return structured_evaluation
        except Exception as e:
            raise Exception(f"Error evaluating response: {str(e)}")

    def _process_questions(self, response: str) -> List[Dict[str, Any]]:
        """Process the LLM response into structured questions."""
        # Here you would implement the logic to parse the LLM response
        # into a structured format. This is a simplified example.
        questions = []
        lines = response.split("\n")
        
        for line in lines:
            if line.strip() and not line.startswith(("1.", "2.", "3.", "4.", "5.")):
                questions.append({
                    "text": line.strip(),
                    "category": "general",  # You would implement logic to categorize questions
                    "difficulty": "medium"  # You would implement logic to determine difficulty
                })
        
        return questions

    def _process_evaluation(self, response: str) -> Dict[str, Any]:
        """Process the LLM response into structured evaluation."""
        # Here you would implement the logic to parse the LLM response
        # into a structured format. This is a simplified example.
        evaluation = {
            "technical_accuracy": 0.0,
            "problem_solving": 0.0,
            "communication": 0.0,
            "understanding": 0.0,
            "feedback": [],
            "suggestions": []
        }
        
        # Process the response to populate the evaluation structure
        # This is where you would implement the actual parsing logic
        
        return evaluation 