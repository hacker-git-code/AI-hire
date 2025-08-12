from typing import List, Dict, Any, Optional
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.chains import LLMChain
from langchain.embeddings import OpenAIEmbeddings
from app.models.candidate import Candidate
from app.models.job import JobPosting, RequiredSkill
from app.core.config import settings
import pinecone
import json
import numpy as np
from datetime import datetime

class AIScreeningService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.1,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY
        )
        self._init_pinecone()
        
    def _init_pinecone(self):
        pinecone.init(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENVIRONMENT
        )
        self.index = pinecone.Index(settings.PINECONE_INDEX_NAME)

    async def evaluate_candidate(self, candidate: Candidate, job: JobPosting) -> Dict[str, Any]:
        """Evaluate a candidate's fit for a job posting with enhanced analysis."""
        
        # Create evaluation prompt with more detailed criteria
        evaluation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert hiring assistant. Evaluate the candidate's fit for the job based on:
            1. Skills match (technical and soft skills)
            2. Experience level and relevance
            3. Education requirements and alignment
            4. Cultural fit indicators
            5. Growth potential
            6. Team compatibility
            7. Leadership potential (if applicable)
            
            Provide a detailed analysis with:
            - Overall match score (0-100)
            - Individual category scores
            - Specific strengths and gaps
            - Development recommendations
            - Risk factors
            - Hiring recommendation
            Format the output as structured JSON."""),
            ("human", """
            Job Title: {job_title}
            Company: {company}
            Required Skills: {required_skills}
            Experience Level: {experience_level}
            Job Description: {job_description}
            
            Candidate Profile:
            Name: {candidate_name}
            Current Position: {current_position}
            Years Experience: {years_experience}
            Skills: {candidate_skills}
            Experience: {candidate_experience}
            Education: {candidate_education}
            """)
        ])
        
        # Format the data
        job_data = {
            "job_title": job.title,
            "company": job.company,
            "required_skills": [f"{skill.name} ({skill.level})" for skill in job.required_skills],
            "experience_level": job.experience_level,
            "job_description": job.description
        }
        
        candidate_data = {
            "candidate_name": f"{candidate.first_name} {candidate.last_name}",
            "current_position": candidate.current_position or "Not specified",
            "years_experience": candidate.years_experience,
            "candidate_skills": [f"{skill.name} ({skill.level})" for skill in candidate.skills],
            "candidate_experience": [f"{exp.position} at {exp.company}: {exp.description}" for exp in candidate.experience],
            "candidate_education": [f"{edu.degree} in {edu.field_of_study} from {edu.institution}" for edu in candidate.education]
        }
        
        # Run evaluation
        chain = LLMChain(llm=self.llm, prompt=evaluation_prompt)
        evaluation = await chain.arun(**job_data, **candidate_data)
        
        # Store evaluation in vector database
        await self._store_evaluation(candidate.id, job.id, evaluation)
        
        return self._parse_evaluation(evaluation)

    async def generate_interview_questions(self, candidate: Candidate, job: JobPosting) -> List[Dict[str, Any]]:
        """Generate tailored interview questions with advanced context awareness."""
        
        question_prompt = ChatPromptTemplate.from_messages([
            ("system", """Generate a comprehensive set of interview questions that will help assess:
            1. Technical skills and knowledge
            2. Problem-solving abilities and approach
            3. Experience relevance and depth
            4. Cultural fit and values
            5. Leadership and collaboration
            6. Growth mindset and learning ability
            7. Communication skills
            
            For each question, provide:
            - The question text
            - Category
            - Difficulty level
            - Expected answer key points
            - Evaluation criteria
            - Follow-up questions
            
            Questions should be specific to the candidate's background and job requirements.
            Format the output as structured JSON."""),
            ("human", """
            Job Requirements: {job_requirements}
            Candidate Background: {candidate_background}
            Interview Type: {interview_type}
            """)
        ])
        
        # Format the data
        job_requirements = {
            "requirements": job.requirements,
            "required_skills": [skill.name for skill in job.required_skills],
            "responsibilities": job.responsibilities
        }
        
        candidate_background = {
            "experience": [f"{exp.position} at {exp.company}: {exp.description}" for exp in candidate.experience],
            "skills": [skill.name for skill in candidate.skills],
            "education": [f"{edu.degree} in {edu.field_of_study}" for edu in candidate.education]
        }
        
        # Generate questions
        chain = LLMChain(llm=self.llm, prompt=question_prompt)
        questions = await chain.arun(
            job_requirements=json.dumps(job_requirements),
            candidate_background=json.dumps(candidate_background),
            interview_type="technical"  # This could be parameterized
        )
        
        return self._parse_questions(questions)

    async def analyze_resume(self, resume_text: str) -> Dict[str, Any]:
        """Analyze resume text with enhanced information extraction."""
        
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """Extract and structure the following information from the resume:
            1. Personal information
            2. Work experience (with detailed analysis)
            3. Education (with relevance assessment)
            4. Skills (with proficiency levels)
            5. Projects (with impact analysis)
            6. Achievements and metrics
            7. Career progression
            8. Industry expertise
            9. Leadership experience
            10. Technical stack proficiency
            
            For each section, provide:
            - Raw extracted information
            - Structured data
            - Confidence scores
            - Potential gaps or inconsistencies
            
            Format the output as structured JSON."""),
            ("human", "Resume text: {resume_text}")
        ])
        
        chain = LLMChain(llm=self.llm, prompt=analysis_prompt)
        analysis = await chain.arun(resume_text=resume_text)
        
        return json.loads(analysis)

    async def _store_evaluation(self, candidate_id: str, job_id: str, evaluation: str) -> None:
        """Store evaluation in vector database for future reference."""
        try:
            # Generate embedding for the evaluation
            embedding = await self.embeddings.aembed_query(evaluation)
            
            # Store in Pinecone
            self.index.upsert(
                vectors=[{
                    "id": f"eval_{candidate_id}_{job_id}_{datetime.utcnow().timestamp()}",
                    "values": embedding,
                    "metadata": {
                        "candidate_id": candidate_id,
                        "job_id": job_id,
                        "evaluation": evaluation,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }]
            )
        except Exception as e:
            print(f"Error storing evaluation: {str(e)}")

    def _parse_evaluation(self, evaluation: str) -> Dict[str, Any]:
        """Parse the evaluation output into a structured format."""
        try:
            return json.loads(evaluation)
        except json.JSONDecodeError:
            # Enhanced fallback parsing
            sections = evaluation.split("\n\n")
            parsed = {
                "raw_evaluation": evaluation,
                "scores": {},
                "recommendations": [],
                "strengths": [],
                "gaps": [],
                "risks": []
            }
            
            for section in sections:
                if "score" in section.lower():
                    try:
                        score = float(section.split(":")[-1].strip())
                        category = section.split(":")[0].strip()
                        parsed["scores"][category] = score
                    except:
                        continue
                elif "recommendation" in section.lower():
                    parsed["recommendations"].append(section.strip())
                elif "strength" in section.lower():
                    parsed["strengths"].append(section.strip())
                elif "gap" in section.lower():
                    parsed["gaps"].append(section.strip())
                elif "risk" in section.lower():
                    parsed["risks"].append(section.strip())
            
            return parsed

    def _parse_questions(self, questions: str) -> List[Dict[str, Any]]:
        """Parse the generated questions into a structured format."""
        try:
            return json.loads(questions)
        except json.JSONDecodeError:
            # Enhanced fallback parsing
            questions_list = []
            current_question = {}
            
            for line in questions.split("\n"):
                line = line.strip()
                if not line:
                    if current_question:
                        questions_list.append(current_question)
                        current_question = {}
                    continue
                
                if line.startswith("Q:") or line.startswith("Question:"):
                    if current_question:
                        questions_list.append(current_question)
                    current_question = {"question": line.split(":", 1)[1].strip()}
                elif line.startswith("Category:"):
                    current_question["category"] = line.split(":", 1)[1].strip()
                elif line.startswith("Difficulty:"):
                    current_question["difficulty"] = line.split(":", 1)[1].strip()
                elif line.startswith("Expected Answer:"):
                    current_question["expected_answer"] = line.split(":", 1)[1].strip()
                elif line.startswith("Criteria:"):
                    current_question["evaluation_criteria"] = line.split(":", 1)[1].strip()
            
            if current_question:
                questions_list.append(current_question)
            
            return questions_list 