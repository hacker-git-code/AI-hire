from typing import Dict, Any, List
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.core.config import settings

class MatchingService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.5,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.cultural_fit_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in cultural fit analysis. Evaluate the alignment between a candidate's profile and a team's culture.
            Consider:
            1. Values and beliefs
            2. Work style preferences
            3. Communication patterns
            4. Team dynamics
            5. Leadership approach
            
            Provide a detailed analysis with specific examples and recommendations."""),
            ("human", "Candidate Profile: {candidate_profile}\nTeam Profile: {team_profile}")
        ])
        
        self.skill_fit_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in skill matching. Analyze the alignment between a candidate's skills and required skills.
            Consider:
            1. Technical proficiency
            2. Experience level
            3. Skill gaps
            4. Learning potential
            5. Growth trajectory
            
            Provide a detailed analysis with specific examples and recommendations."""),
            ("human", "Candidate Skills: {candidate_skills}\nRequired Skills: {required_skills}")
        ])
        
        self.performance_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in performance prediction. Analyze a candidate's potential performance in a role.
            Consider:
            1. Past performance indicators
            2. Skill alignment
            3. Cultural fit
            4. Growth potential
            5. Risk factors
            
            Provide a detailed prediction with specific examples and recommendations."""),
            ("human", "Candidate Profile: {candidate_profile}\nRole Requirements: {role_requirements}")
        ])

    def analyze_cultural_fit(
        self,
        candidate_profile: Dict[str, Any],
        team_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze cultural fit between candidate and team."""
        try:
            # Format the prompt
            formatted_prompt = self.cultural_fit_prompt.format_messages(
                candidate_profile=str(candidate_profile),
                team_profile=str(team_profile)
            )
            
            # Get the LLM response
            response = self.llm(formatted_prompt)
            
            # Process and structure the analysis
            analysis = self._process_cultural_fit(response.content)
            
            return analysis
        except Exception as e:
            raise Exception(f"Error analyzing cultural fit: {str(e)}")

    def analyze_skill_fit(
        self,
        candidate_skills: List[str],
        required_skills: List[str]
    ) -> Dict[str, Any]:
        """Analyze skill fit between candidate and requirements."""
        try:
            # Format the prompt
            formatted_prompt = self.skill_fit_prompt.format_messages(
                candidate_skills=str(candidate_skills),
                required_skills=str(required_skills)
            )
            
            # Get the LLM response
            response = self.llm(formatted_prompt)
            
            # Process and structure the analysis
            analysis = self._process_skill_fit(response.content)
            
            return analysis
        except Exception as e:
            raise Exception(f"Error analyzing skill fit: {str(e)}")

    def predict_performance(
        self,
        candidate_profile: Dict[str, Any],
        role_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict candidate performance in the role."""
        try:
            # Format the prompt
            formatted_prompt = self.performance_prompt.format_messages(
                candidate_profile=str(candidate_profile),
                role_requirements=str(role_requirements)
            )
            
            # Get the LLM response
            response = self.llm(formatted_prompt)
            
            # Process and structure the prediction
            prediction = self._process_performance(response.content)
            
            return prediction
        except Exception as e:
            raise Exception(f"Error predicting performance: {str(e)}")

    def _process_cultural_fit(self, response: str) -> Dict[str, Any]:
        """Process the LLM response into structured cultural fit analysis."""
        # Here you would implement the logic to parse the LLM response
        # into a structured format. This is a simplified example.
        analysis = {
            "alignment_score": 0.0,
            "strengths": [],
            "concerns": [],
            "recommendations": []
        }
        
        # Process the response to populate the analysis structure
        # This is where you would implement the actual parsing logic
        
        return analysis

    def _process_skill_fit(self, response: str) -> Dict[str, Any]:
        """Process the LLM response into structured skill fit analysis."""
        # Here you would implement the logic to parse the LLM response
        # into a structured format. This is a simplified example.
        analysis = {
            "match_score": 0.0,
            "matching_skills": [],
            "missing_skills": [],
            "recommendations": []
        }
        
        # Process the response to populate the analysis structure
        # This is where you would implement the actual parsing logic
        
        return analysis

    def _process_performance(self, response: str) -> Dict[str, Any]:
        """Process the LLM response into structured performance prediction."""
        # Here you would implement the logic to parse the LLM response
        # into a structured format. This is a simplified example.
        prediction = {
            "performance_score": 0.0,
            "strengths": [],
            "risks": [],
            "recommendations": []
        }
        
        # Process the response to populate the prediction structure
        # This is where you would implement the actual parsing logic
        
        return prediction 