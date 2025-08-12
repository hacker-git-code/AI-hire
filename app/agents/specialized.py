from typing import Any, Dict, List, Optional
from langchain.agents import AgentType, initialize_agent, Tool
from langchain.tools import BaseTool
from langchain.chains import LLMChain
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder
)
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agents.base import BaseAgent
from app.tools.resume import ResumeParserTool
from app.tools.interview import InterviewTool
from app.tools.matching import MatchingTool
from app.tools.coordination import CoordinationTool
from app.core.config import settings
from app.services.gemini import GeminiService
import logging
import json

logger = logging.getLogger(__name__)

class ScreenerAgent(BaseAgent):
    def __init__(self, model_name: str = "gemini-pro"):
        self.gemini = GeminiService()
        tools = [
            ResumeParserTool(),
            MatchingTool(),
            self._create_analysis_tool()
        ]
        super().__init__(
            name="Screener",
            role="Resume Analysis & Candidate Triage Specialist",
            tools=tools,
            temperature=0.3,
            model_name=model_name,
            max_memory_items=15
        )
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.3,
            google_api_key=settings.GOOGLE_API_KEY
        )
        self.resume_evaluation_criteria = {
            "technical_skills": {"weight": 0.3, "description": "Relevant technical skills and experience"},
            "experience_level": {"weight": 0.25, "description": "Years and relevance of experience"},
            "education": {"weight": 0.15, "description": "Educational background and certifications"},
            "achievements": {"weight": 0.2, "description": "Notable achievements and impact"},
            "cultural_fit": {"weight": 0.1, "description": "Alignment with company values"}
        }

    def _create_analysis_tool(self) -> Tool:
        """Create a tool for advanced resume analysis."""
        return Tool(
            name="advanced_resume_analysis",
            func=self._analyze_resume,
            description="""Useful for in-depth analysis of resumes. 
            Input should be a JSON string with 'resume_text' and 'job_description' keys.
            Returns a structured analysis of the candidate's qualifications."""
        )

    async def _analyze_resume(self, input_str: str) -> str:
        """Perform advanced analysis of a resume against a job description using Gemini."""
        try:
            data = json.loads(input_str)
            resume_text = data.get('resume_text', '')
            job_description = data.get('job_description', '')
            
            if not resume_text or not job_description:
                return json.dumps({
                    "error": "Missing resume_text or job_description in input",
                    "status": "error"
                })
            
            # Use Gemini to analyze the resume
            analysis = await self.gemini.analyze_resume(resume_text, job_description)
            return json.dumps({
                "status": "success",
                "analysis": analysis
            })
            
        except Exception as e:
            error_msg = f"Error in resume analysis: {str(e)}"
            logger.error(error_msg)
            return json.dumps({
                "status": "error",
                "error": error_msg
            })

    def _get_role_description(self) -> str:
        return """You are an expert in analyzing resumes, evaluating candidate qualifications, and performing initial screening.
        
        Key Responsibilities:
        1. Extract and validate candidate information with high accuracy
        2. Match skills and experience to job requirements using weighted scoring
        3. Identify potential red flags and areas of concern
        4. Provide initial candidate ranking with justification
        5. Generate targeted screening questions
        6. Evaluate cultural fit based on company values
        7. Provide structured feedback on candidate strengths and weaknesses
        
        Evaluation Criteria:
        """ + "\n".join(
            f"- {k}: {v['description']} (Weight: {v['weight']*100}%)" 
            for k, v in self.resume_evaluation_criteria.items()
        )

    def _create_agent(self) -> Any:
        # Create a custom prompt template
        system_message = SystemMessage(content=self.get_system_prompt())
        human_template = "{input}"
        human_message = HumanMessagePromptTemplate.from_template(human_template)
        
        prompt = ChatPromptTemplate.from_messages([
            system_message,
            MessagesPlaceholder(variable_name="chat_history"),
            human_message,
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Initialize the agent with the custom prompt
        agent = initialize_agent(
            self.tools,
            self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            memory=self.memory,
            agent_kwargs={
                'system_message': system_message,
                'human_message': human_template,
                'input_variables': ['input', 'chat_history', 'agent_scratchpad']
            }
        )
        
        return agent

class InterviewerAgent(BaseAgent):
    def __init__(self, model_name: str = "gpt-4-turbo-preview"):
        tools = [
            InterviewTool(),
            MatchingTool(),
            self._create_evaluation_tool()
        ]
        super().__init__(
            name="Interviewer",
            role="Senior Technical & Behavioral Interviewer",
            tools=tools,
            temperature=0.7,
            model_name=model_name,
            max_memory_items=20
        )
        self.interview_framework = {
            "technical": {
                "weight": 0.4,
                "areas": ["problem_solving", "technical_knowledge", "practical_skills"]
            },
            "behavioral": {
                "weight": 0.3,
                "areas": ["communication", "teamwork", "leadership", "conflict_resolution"]
            },
            "cultural_fit": {
                "weight": 0.2,
                "areas": ["values_alignment", "work_style", "motivation"]
            },
            "growth_potential": {
                "weight": 0.1,
                "areas": ["learning_ability", "adaptability", "career_goals"]
            }
        }

    def _create_evaluation_tool(self) -> Tool:
        """Create a tool for evaluating interview responses."""
        return Tool(
            name="evaluate_response",
            func=self._evaluate_response,
            description="""Useful for evaluating candidate responses during interviews.
            Input should be a JSON string with 'question', 'response', and 'evaluation_criteria'.
            Returns a structured evaluation of the response."""
        )

    def _evaluate_response(self, input_str: str) -> str:
        """Evaluate a candidate's response to an interview question."""
        try:
            import json
            data = json.loads(input_str)
            question = data.get('question', '')
            response = data.get('response', '')
            criteria = data.get('evaluation_criteria', {})
            
            if not question or not response:
                return "Error: Missing question or response in input"
                
            # Create a prompt for response evaluation
            prompt = f"""Evaluate the following interview response:
            
            QUESTION: {question}
            
            CANDIDATE RESPONSE:
            {response}
            
            EVALUATION CRITERIA:
            {json.dumps(criteria, indent=2) if criteria else 'No specific criteria provided'}
            
            Provide a detailed evaluation including:
            1. Relevance to the question
            2. Depth of response
            3. Evidence of skills/experience
            4. Communication effectiveness
            5. Areas for follow-up
            6. Overall rating (1-5)
            """
            
            # Use the LLM to evaluate the response
            evaluation = self.llm.predict(prompt)
            return evaluation
            
        except Exception as e:
            logger.error(f"Error in response evaluation: {str(e)}")
            return f"Error evaluating response: {str(e)}"

    def _get_role_description(self) -> str:
        framework_desc = "\n".join(
            f"- {cat.capitalize()} ({data['weight']*100}%): {', '.join(data['areas'])}"
            for cat, data in self.interview_framework.items()
        )
        
        return f"""You are an expert interviewer skilled in conducting comprehensive technical and behavioral interviews.
        
        Interview Framework:
        {framework_desc}
        
        Key Responsibilities:
        1. Ask probing, relevant questions based on the candidate's background
        2. Adapt questions based on previous responses
        3. Evaluate both technical and soft skills
        4. Assess cultural fit and team compatibility
        5. Provide detailed, structured feedback
        6. Maintain professional and unbiased throughout the interview
        7. Identify strengths, weaknesses, and potential red flags
        
        Always be respectful, professional, and focused on gathering meaningful insights."""

    def _create_agent(self) -> Any:
        # Create a custom prompt template
        system_message = SystemMessage(content=self.get_system_prompt())
        human_template = """Let's conduct an interview. Here's the context: {input}
        
        Please provide your response or say 'I need more information' if the context is unclear."""
        human_message = HumanMessagePromptTemplate.from_template(human_template)
        
        prompt = ChatPromptTemplate.from_messages([
            system_message,
            MessagesPlaceholder(variable_name="chat_history"),
            human_message,
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Initialize the agent with the custom prompt
        agent = initialize_agent(
            self.tools,
            self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            memory=self.memory,
            agent_kwargs={
                'system_message': system_message,
                'human_message': human_template,
                'input_variables': ['input', 'chat_history', 'agent_scratchpad']
            }
        )
        
        return agent

class MatcherAgent(BaseAgent):
    def __init__(self, model_name: str = "gpt-4-turbo-preview"):
        tools = [
            MatchingTool(),
            CoordinationTool(),
            self._create_cultural_fit_tool(),
            self._create_skill_gap_analysis_tool(),
            self._create_team_compatibility_tool()
        ]
        super().__init__(
            name="Matcher",
            role="Advanced Candidate Matching & Fit Analysis",
            tools=tools,
            temperature=0.3,
            model_name=model_name,
            max_memory_items=20
        )
        self.matching_criteria = {
            "technical_skills": {"weight": 0.35, "description": "Alignment of candidate skills with job requirements"},
            "experience_level": {"weight": 0.25, "description": "Relevance and depth of experience"},
            "cultural_fit": {"weight": 0.2, "description": "Alignment with company values and team culture"},
            "growth_potential": {"weight": 0.1, "description": "Potential for growth and development"},
            "compensation_alignment": {"weight": 0.1, "description": "Alignment of compensation expectations"}
        }

    def _create_cultural_fit_tool(self) -> Tool:
        """Create a tool for analyzing cultural fit."""
        return Tool(
            name="analyze_cultural_fit",
            func=self._analyze_cultural_fit,
            description="""Analyze cultural fit between a candidate and company/team.
            Input should be a JSON string with 'candidate_profile' and 'company_culture' keys.
            Returns a detailed cultural fit analysis."""
        )

    def _create_skill_gap_analysis_tool(self) -> Tool:
        """Create a tool for analyzing skill gaps."""
        return Tool(
            name="analyze_skill_gaps",
            func=self._analyze_skill_gaps,
            description="""Analyze skill gaps between candidate and job requirements.
            Input should be a JSON string with 'candidate_skills' and 'required_skills' keys.
            Returns a detailed skill gap analysis."""
        )

    def _create_team_compatibility_tool(self) -> Tool:
        """Create a tool for assessing team compatibility."""
        return Tool(
            name="assess_team_compatibility",
            func=self._assess_team_compatibility,
            description="""Assess compatibility between candidate and team.
            Input should be a JSON string with 'candidate_profile' and 'team_profile' keys.
            Returns a team compatibility assessment."""
        )

    def _analyze_cultural_fit(self, input_str: str) -> str:
        """Analyze cultural fit between candidate and company/team."""
        try:
            import json
            data = json.loads(input_str)
            candidate_profile = data.get('candidate_profile', '')
            company_culture = data.get('company_culture', '')
            
            if not candidate_profile or not company_culture:
                return "Error: Missing candidate_profile or company_culture in input"
                
            prompt = f"""Analyze the cultural fit between the candidate and company:
            
            CANDIDATE PROFILE:
            {candidate_profile}
            
            COMPANY CULTURE:
            {company_culture}
            
            Provide a detailed analysis including:
            1. Cultural alignment score (1-100)
            2. Key cultural strengths
            3. Potential cultural challenges
            4. Recommendations for onboarding
            5. Suggested interview questions to assess cultural fit
            """
            
            return self.llm.predict(prompt)
            
        except Exception as e:
            logger.error(f"Error in cultural fit analysis: {str(e)}")
            return f"Error analyzing cultural fit: {str(e)}"

    def _analyze_skill_gaps(self, input_str: str) -> str:
        """Analyze skill gaps between candidate and job requirements."""
        try:
            import json
            data = json.loads(input_str)
            candidate_skills = data.get('candidate_skills', [])
            required_skills = data.get('required_skills', [])
            
            if not candidate_skills or not required_skills:
                return "Error: Missing candidate_skills or required_skills in input"
                
            prompt = f"""Analyze the skill gaps between the candidate and job requirements:
            
            CANDIDATE SKILLS:
            {json.dumps(candidate_skills, indent=2)}
            
            REQUIRED SKILLS:
            {json.dumps(required_skills, indent=2)}
            
            Provide a detailed analysis including:
            1. Skill match percentage
            2. Strong areas
            3. Missing skills
            4. Development areas
            5. Recommended training/learning resources
            """
            
            return self.llm.predict(prompt)
            
        except Exception as e:
            logger.error(f"Error in skill gap analysis: {str(e)}")
            return f"Error analyzing skill gaps: {str(e)}"

    def _assess_team_compatibility(self, input_str: str) -> str:
        """Assess compatibility between candidate and team."""
        try:
            import json
            data = json.loads(input_str)
            candidate_profile = data.get('candidate_profile', '')
            team_profile = data.get('team_profile', '')
            
            if not candidate_profile or not team_profile:
                return "Error: Missing candidate_profile or team_profile in input"
                
            prompt = f"""Assess the compatibility between the candidate and team:
            
            CANDIDATE PROFILE:
            {candidate_profile}
            
            TEAM PROFILE:
            {team_profile}
            
            Provide a detailed assessment including:
            1. Team compatibility score (1-100)
            2. Potential synergies
            3. Possible areas of conflict
            4. Recommendations for team integration
            5. Suggested team-building activities
            """
            
            return self.llm.predict(prompt)
            
        except Exception as e:
            logger.error(f"Error in team compatibility assessment: {str(e)}")
            return f"Error assessing team compatibility: {str(e)}"

    def _get_role_description(self) -> str:
        return f"""You are an expert in matching candidates to job opportunities and teams.
        
        Your responsibilities include:
        1. Analyzing candidate qualifications against job requirements
        2. Evaluating cultural fit with company values and team dynamics
        3. Identifying skill gaps and development opportunities
        4. Predicting candidate success in the role
        5. Providing data-driven matching recommendations
        
        Matching Criteria (with weights):
        {json.dumps({k: f"{v['description']} ({v['weight']*100}%)" for k, v in self.matching_criteria.items()}, indent=2)}
        
        Always provide clear, objective, and actionable insights to support hiring decisions."""

    def _create_agent(self) -> Any:
        system_message = SystemMessage(content=self.get_system_prompt())
        human_template = """Match candidate to job: {input}
        
        Available tools:
        - analyze_cultural_fit: Analyze cultural fit between candidate and company
        - analyze_skill_gaps: Analyze skill gaps between candidate and job requirements
        - assess_team_compatibility: Assess compatibility between candidate and team
        
        Example input for analyze_cultural_fit:
        {{"candidate_profile": "...", "company_culture": "..."}}"""
        human_message = HumanMessagePromptTemplate.from_template(human_template)
        
        prompt = ChatPromptTemplate.from_messages([
            system_message,
            MessagesPlaceholder(variable_name="chat_history"),
            human_message,
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = initialize_agent(
            self.tools,
            self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            memory=self.memory,
            agent_kwargs={
                'prefix': system_message.content,
                'human_message': human_template,
                'input_variables': ['input', 'chat_history', 'agent_scratchpad']
            }
        )
        
        return agent

class CoordinatorAgent(BaseAgent):
    def __init__(self, model_name: str = "gpt-4-turbo-preview"):
        tools = [
            CoordinationTool(),
            InterviewTool(),
            MatchingTool(),
            self._create_workflow_automation_tool(),
            self._create_advanced_reporting_tool(),
            self._create_interview_scheduler_tool(),
            self._create_collaboration_tool()
        ]
        super().__init__(
            name="Coordinator",
            role="Advanced Hiring Workflow Orchestrator",
            tools=tools,
            temperature=0.2,  # Lower temperature for more consistent workflow management
            model_name=model_name,
            max_memory_items=50  # Increased for better context retention
        )
        
        # Define workflow stages with SLAs and owners
        self.workflow_stages = {
            "Sourcing": {"sla_days": 5, "default_owner": "Recruiter"},
            "Screening": {"sla_days": 3, "default_owner": "Recruiter"},
            "Technical_Assessment": {"sla_days": 7, "default_owner": "Hiring Manager"},
            "Interviews": {
                "sub_stages": ["HR", "Technical", "Team Fit", "Final"],
                "sla_days": 14,
                "default_owner": "Hiring Team"
            },
            "Offer_Negotiation": {"sla_days": 5, "default_owner": "HR"},
            "Onboarding": {"sla_days": 30, "default_owner": "People Ops"}
        }
        
        # Initialize candidate pipeline with enhanced tracking
        self.candidate_pipeline = {}
        
        # Define comprehensive performance metrics
        self.performance_metrics = {
            "time_to_hire": {
                "target": 30, 
                "unit": "days",
                "description": "Average time from application to offer acceptance"
            },
            "candidate_experience": {
                "target": 4.5, 
                "unit": "stars (1-5)",
                "description": "Candidate satisfaction score"
            },
            "offer_acceptance_rate": {
                "target": 80, 
                "unit": "%",
                "description": "Percentage of offers accepted"
            },
            "hiring_manager_satisfaction": {
                "target": 4.5, 
                "unit": "stars (1-5)",
                "description": "Hiring manager satisfaction with the process"
            },
            "diversity_metrics": {
                "target": "N/A",
                "unit": "%",
                "description": "Diversity in candidate pipeline"
            },
            "cost_per_hire": {
                "target": "TBD",
                "unit": "USD",
                "description": "Average cost per hire"
            }
        }
        
        # Templates for common communications
        self.communication_templates = {
            "interview_schedule": {
                "subject": "Interview Invitation: {position} at {company}",
                "body": """Dear {candidate_name},
                
We're excited to invite you for a {interview_type} interview for the {position} position at {company}.

Date: {date}
Time: {time}
Location: {location}
Interviewers: {interviewers}

Please confirm your availability or suggest alternative times if needed.

Best regards,
{your_name}"""
            },
            "offer_letter": {
                "subject": "Job Offer: {position} at {company}",
                "body": """Dear {candidate_name},
                
We are pleased to offer you the position of {position} at {company}.

Position: {position}
Start Date: {start_date}
Salary: {salary}
Benefits: {benefits}

Please review the attached offer letter and let us know if you have any questions.

We look forward to welcoming you to the team!

Best regards,
{your_name}"""
            }
        }

    def _create_workflow_automation_tool(self) -> Tool:
        """Create a tool for automating hiring workflows."""
        return Tool(
            name="automate_workflow",
            func=self._automate_workflow,
            description="""Automate hiring workflow tasks and transitions.
            Input should be a JSON string with 'action', 'candidate_id', and optional parameters.
            Supported actions: advance_stage, send_reminder, schedule_interview, collect_feedback.
            Returns status of the workflow automation."""
        )

    def _create_advanced_reporting_tool(self) -> Tool:
        """Create a tool for generating advanced hiring reports."""
        return Tool(
            name="generate_advanced_report",
            func=self._generate_advanced_report,
            description="""Generate comprehensive hiring reports with analytics.
            Input should be a JSON string with 'report_type', 'time_period', 'filters', and 'metrics'.
            Returns a detailed report with visualizations and insights."""
        )
        
    def _create_interview_scheduler_tool(self) -> Tool:
        """Create a tool for scheduling interviews."""
        return Tool(
            name="schedule_interview",
            func=self._schedule_interview,
            description="""Schedule interviews with candidates and interviewers.
            Input should be a JSON string with 'candidate_id', 'interview_type', 
            'interviewers', 'preferred_dates', and 'duration_minutes'.
            Returns scheduling details and calendar invites."""
        )
        
    def _create_collaboration_tool(self) -> Tool:
        """Create a tool for team collaboration and communication."""
        return Tool(
            name="collaborate",
            func=self._collaborate,
            description="""Facilitate team collaboration during the hiring process.
            Input should be a JSON string with 'action', 'participants', 'message', and 'context'.
            Supported actions: start_thread, add_comment, share_update, request_feedback.
            Returns collaboration status and thread information."""
        )
        
    def _automate_workflow(self, input_str: str) -> str:
        """Automate hiring workflow tasks and transitions."""
        try:
            import json
            from datetime import datetime, timedelta
            
            data = json.loads(input_str)
            action = data.get('action')
            candidate_id = data.get('candidate_id')
            
            if not action or not candidate_id:
                return "Error: Missing required parameters (action, candidate_id)"
                
            if candidate_id not in self.candidate_pipeline:
                self.candidate_pipeline[candidate_id] = {
                    "current_stage": "Sourcing",
                    "stage_history": [{"stage": "Sourcing", "timestamp": datetime.now().isoformat()}],
                    "notes": [],
                    "interviews": [],
                    "documents": [],
                    "metrics": {}
                }
                
            candidate = self.candidate_pipeline[candidate_id]
            
            if action == "advance_stage":
                return self._advance_candidate_stage(candidate_id, candidate, data.get('next_stage'))
                
            elif action == "send_reminder":
                return self._send_workflow_reminder(candidate_id, candidate, data.get('reminder_type'))
                
            elif action == "collect_feedback":
                return self._collect_interview_feedback(candidate_id, candidate, data.get('interview_id'))
                
            else:
                return f"Unknown action: {action}. Valid actions are: advance_stage, send_reminder, collect_feedback"
                
        except Exception as e:
            logger.error(f"Error in workflow automation: {str(e)}")
            return f"Error in workflow automation: {str(e)}"
            
    def _generate_advanced_report(self, input_str: str) -> str:
        """Generate comprehensive hiring reports with analytics."""
        try:
            import json
            from datetime import datetime, timedelta
            
            data = json.loads(input_str)
            report_type = data.get('report_type', 'pipeline_overview')
            time_period = data.get('time_period', '30d')
            filters = data.get('filters', {})
            
            # Calculate date range
            end_date = datetime.now()
            if time_period == '7d':
                start_date = end_date - timedelta(days=7)
            elif time_period == '30d':
                start_date = end_date - timedelta(days=30)
            elif time_period == '90d':
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=30)  # Default to 30 days
            
            # Generate report based on type
            if report_type == 'pipeline_overview':
                return self._generate_pipeline_report(start_date, end_date, filters)
            elif report_type == 'time_to_hire':
                return self._generate_time_to_hire_report(start_date, end_date, filters)
            elif report_type == 'diversity':
                return self._generate_diversity_report(start_date, end_date, filters)
            else:
                return f"Unknown report type: {report_type}"
                
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return f"Error generating report: {str(e)}"
            
    def _schedule_interview(self, input_str: str) -> str:
        """Schedule an interview with a candidate."""
        try:
            import json
            from datetime import datetime, timedelta
            
            data = json.loads(input_str)
            candidate_id = data.get('candidate_id')
            interview_type = data.get('interview_type')
            interviewers = data.get('interviewers', [])
            preferred_dates = data.get('preferred_dates', [])
            duration_minutes = data.get('duration_minutes', 60)
            
            if not candidate_id or not interview_type or not interviewers or not preferred_dates:
                return "Error: Missing required parameters (candidate_id, interview_type, interviewers, preferred_dates)"
                
            # In a real implementation, this would integrate with a calendar system
            # For now, we'll just return a mock response
            scheduled_date = datetime.fromisoformat(preferred_dates[0]) if preferred_dates else datetime.now() + timedelta(days=2)
            
            interview = {
                "id": f"int_{len(self.candidate_pipeline.get(candidate_id, {}).get('interviews', [])) + 1}",
                "type": interview_type,
                "scheduled_time": scheduled_date.isoformat(),
                "duration_minutes": duration_minutes,
                "interviewers": interviewers,
                "status": "scheduled",
                "meeting_link": f"https://meet.example.com/room/{candidate_id[:8]}"
            }
            
            if candidate_id not in self.candidate_pipeline:
                self.candidate_pipeline[candidate_id] = {
                    "current_stage": "Scheduling",
                    "interviews": []
                }
                
            self.candidate_pipeline[candidate_id]["interviews"].append(interview)
            
            return json.dumps({
                "status": "success",
                "interview": interview,
                "message": "Interview scheduled successfully"
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error scheduling interview: {str(e)}")
            return f"Error scheduling interview: {str(e)}"
            
    def _collaborate(self, input_str: str) -> str:
        """Facilitate team collaboration during the hiring process.
        
        Args:
            input_str: JSON string containing collaboration details with keys:
                     - action: The collaboration action to perform
                     - participants: List of participant identifiers
                     - message: Optional message content
                     - context: Additional context for the action
                     
        Returns:
            str: JSON string with collaboration results or error message
        """
        try:
            import json
            from datetime import datetime
            
            # Parse input data
            try:
                data = json.loads(input_str)
            except json.JSONDecodeError:
                return json.dumps({
                    "status": "error",
                    "message": "Invalid JSON input"
                }, indent=2)
            
            # Extract and validate required fields
            action = data.get('action')
            participants = data.get('participants', [])
            message = data.get('message', '')
            context = data.get('context', {})
            
            if not action or not participants:
                return json.dumps({
                    "status": "error",
                    "message": "Missing required parameters (action, participants)"
                }, indent=2)
            
            # Handle different collaboration actions
            if action == "start_thread":
                try:
                    thread_id = f"thread_{len(self.candidate_pipeline) + 1}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                    thread_info = {
                        "id": thread_id,
                        "created_at": datetime.utcnow().isoformat(),
                        "participants": participants,
                        "messages": [],
                        "status": "active"
                    }
                    
                    # In a real implementation, store the thread in a database
                    if not hasattr(self, '_collaboration_threads'):
                        self._collaboration_threads = {}
                    self._collaboration_threads[thread_id] = thread_info
                    
                    return json.dumps({
                        "status": "success",
                        "thread_id": thread_id,
                        "message": f"New collaboration thread created with ID: {thread_id}",
                        "timestamp": datetime.utcnow().isoformat()
                    }, indent=2)
                    
                except Exception as e:
                    logger.error(f"Error creating thread: {str(e)}")
                    return json.dumps({
                        "status": "error",
                        "message": f"Failed to create thread: {str(e)}"
                    }, indent=2)
                
            elif action == "add_comment":
                if not message:
                    return json.dumps({
                        "status": "error",
                        "message": "Message is required for add_comment action"
                    }, indent=2)
                    
                thread_id = context.get('thread_id')
                if not thread_id or not hasattr(self, '_collaboration_threads') or thread_id not in self._collaboration_threads:
                    return json.dumps({
                        "status": "error",
                        "message": f"Invalid or missing thread_id: {thread_id}"
                    }, indent=2)
                
                try:
                    comment = {
                        "id": f"comment_{len(self._collaboration_threads[thread_id]['messages']) + 1}",
                        "author": context.get('author', 'system'),
                        "message": message,
                        "timestamp": datetime.utcnow().isoformat(),
                        "metadata": {
                            "type": context.get('type', 'comment'),
                            "status": context.get('status')
                        }
                    }
                    
                    self._collaboration_threads[thread_id]['messages'].append(comment)
                    
                    return json.dumps({
                        "status": "success",
                        "message": "Comment added to thread",
                        "comment_id": comment['id'],
                        "thread_id": thread_id,
                        "timestamp": comment['timestamp']
                    }, indent=2)
                    
                except Exception as e:
                    logger.error(f"Error adding comment: {str(e)}")
                    return json.dumps({
                        "status": "error",
                        "message": f"Failed to add comment: {str(e)}"
                    }, indent=2)
                
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Unknown action: {action}",
                    "valid_actions": ["start_thread", "add_comment"]
                }, indent=2)
                
        except Exception as e:
            logger.error(f"Unexpected error in collaboration: {str(e)}")
            return json.dumps({
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}"
            }, indent=2)

    def _advance_candidate_stage(self, candidate_id: str, candidate: dict, next_stage: str = None) -> str:
        """Advance a candidate to the next stage in the hiring process."""
        try:
            from datetime import datetime
            
            current_stage = candidate.get("current_stage", "Sourcing")
            
            if not next_stage:
                # Get next stage from workflow
                stage_keys = list(self.workflow_stages.keys())
                current_index = stage_keys.index(current_stage) if current_stage in stage_keys else -1
                
                if current_index < len(stage_keys) - 1:
                    next_stage = stage_keys[current_index + 1]
                else:
                    return f"Candidate {candidate_id} is already at the final stage ({current_stage})."
            
            # Update candidate stage
            candidate["current_stage"] = next_stage
            candidate["stage_history"].append({
                "stage": next_stage,
                "timestamp": datetime.now().isoformat(),
                "action": "advanced"
            })
            
            # Update metrics
            time_in_previous_stage = self._calculate_time_in_stage(candidate)
            if "metrics" not in candidate:
                candidate["metrics"] = {}
            candidate["metrics"][f"time_in_{current_stage}"] = time_in_previous_stage
            
            return f"Moved candidate {candidate_id} from {current_stage} to {next_stage} stage."
            
        except Exception as e:
            logger.error(f"Error advancing candidate stage: {str(e)}")
            return f"Error advancing candidate stage: {str(e)}"
    
    def _send_workflow_reminder(self, candidate_id: str, candidate: dict, reminder_type: str = None) -> str:
        """Send a reminder for a specific workflow action."""
        try:
            current_stage = candidate.get("current_stage", "Unknown")
            
            if not reminder_type:
                reminder_type = "default"
                
            # In a real implementation, this would send an actual email/notification
            return json.dumps({
                "status": "success",
                "message": f"Reminder sent for candidate {candidate_id} in stage {current_stage}",
                "reminder_type": reminder_type,
                "timestamp": datetime.now().isoformat()
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error sending reminder: {str(e)}")
            return f"Error sending reminder: {str(e)}"
    
    def _collect_interview_feedback(self, candidate_id: str, candidate: dict, interview_id: str = None) -> str:
        """Collect feedback for a completed interview."""
        try:
            interviews = candidate.get("interviews", [])
            
            if not interviews:
                return f"No interviews found for candidate {candidate_id}"
                
            if interview_id:
                # Find specific interview
                interview = next((i for i in interviews if i.get("id") == interview_id), None)
                if not interview:
                    return f"Interview {interview_id} not found for candidate {candidate_id}"
                interviews = [interview]
            
            # In a real implementation, this would collect feedback from interviewers
            feedback = []
            for interview in interviews:
                feedback.append({
                    "interview_id": interview.get("id"),
                    "type": interview.get("type"),
                    "status": "feedback_collected",
                    "timestamp": datetime.now().isoformat(),
                    "summary": f"Feedback collected for {interview.get('type')} interview"
                })
            
            return json.dumps({
                "status": "success",
                "candidate_id": candidate_id,
                "feedback": feedback
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error collecting interview feedback: {str(e)}")
            return f"Error collecting interview feedback: {str(e)}"
    
    def _generate_pipeline_report(self, start_date: datetime, end_date: datetime, filters: dict) -> str:
        """Generate a pipeline overview report."""
        try:
            # In a real implementation, this would query a database
            # For now, we'll return sample data
            report = {
                "report_type": "pipeline_overview",
                "time_period": f"{start_date.date()} to {end_date.date()}",
                "total_candidates": len(self.candidate_pipeline),
                "candidates_by_stage": {
                    stage: sum(1 for c in self.candidate_pipeline.values() 
                              if c.get("current_stage") == stage)
                    for stage in self.workflow_stages
                },
                "metrics": {
                    "average_time_in_pipeline": "15 days",
                    "conversion_rate": "25%",
                    "top_sources": ["LinkedIn", "Company Website", "Referrals"]
                }
            }
            
            return json.dumps(report, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Error generating pipeline report: {str(e)}")
            return f"Error generating pipeline report: {str(e)}"
    
    def _generate_time_to_hire_report(self, start_date: datetime, end_date: datetime, filters: dict) -> str:
        """Generate a time-to-hire report."""
        try:
            # In a real implementation, this would analyze actual hiring data
            report = {
                "report_type": "time_to_hire",
                "time_period": f"{start_date.date()} to {end_date.date()}",
                "average_time_to_hire": "27 days",
                "time_by_stage": {
                    stage: f"{i * 2 + 3} days" 
                    for i, stage in enumerate(self.workflow_stages)
                },
                "benchmarks": {
                    "industry_average": "32 days",
                    "company_goal": "30 days"
                }
            }
            
            return json.dumps(report, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Error generating time-to-hire report: {str(e)}")
            return f"Error generating time-to-hire report: {str(e)}"
    
    def _generate_diversity_report(self, start_date: datetime, end_date: datetime, filters: dict) -> str:
        """Generate a diversity and inclusion report."""
        try:
            # In a real implementation, this would analyze demographic data
            report = {
                "report_type": "diversity",
                "time_period": f"{start_date.date()} to {end_date.date()}",
                "diversity_metrics": {
                    "gender": {
                        "male": "55%",
                        "female": "42%",
                        "non_binary": "3%"
                    },
                    "ethnicity": {
                        "white": "60%",
                        "black": "15%",
                        "asian": "15%",
                        "hispanic": "8%",
                        "other": "2%"
                    },
                    "age_distribution": {
                        "18-24": "10%",
                        "25-34": "45%",
                        "35-44": "30%",
                        "45-54": "10%",
                        "55+": "5%"
                    }
                },
                "insights": [
                    "Good gender balance in the candidate pool",
                    "Opportunity to increase representation in technical roles",
                    "Consider targeted outreach to underrepresented groups"
                ]
            }
            
            return json.dumps(report, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Error generating diversity report: {str(e)}")
            return f"Error generating diversity report: {str(e)}"
    
    def _calculate_time_in_stage(self, candidate: dict) -> str:
        """Calculate time spent in current stage.
        
        Args:
            candidate: Dictionary containing candidate data with stage_history
            
        Returns:
            str: Formatted string with time in current stage (e.g., "2d 4h 30m")
        """
        from datetime import datetime
        
        # Safely access dictionary with .get() to avoid KeyError
        if not candidate.get("stage_history") or not candidate.get("current_stage"):
            return "N/A"
            
        current_stage = candidate["current_stage"]
        stage_entries = [h for h in candidate["stage_history"] if h.get("stage") == current_stage]
        
        if not stage_entries:
            return "N/A"
            
        try:
            # Find the most recent entry for the current stage
            latest_entry = max(
                (entry for entry in stage_entries if entry.get("timestamp")),
                key=lambda x: x["timestamp"],
                default=None
            )
            
            if not latest_entry:
                return "N/A"
                
            # Calculate time difference
            time_in_stage = datetime.now() - datetime.fromisoformat(latest_entry["timestamp"])
            
            # Convert to days, hours, minutes
            days = time_in_stage.days
            hours, remainder = divmod(time_in_stage.seconds, 3600)
            minutes = remainder // 60
            
            return f"{days}d {hours}h {minutes}m"
            
        except (ValueError, KeyError) as e:
            logger.error(f"Error calculating time in stage: {str(e)}")
            return "N/A"

    def _generate_report(self, input_str: str) -> str:
        """Generate a hiring process report."""
        try:
            import json
            from datetime import datetime, timedelta
            
            data = json.loads(input_str)
            time_period = data.get('time_period', 'last_30_days')
            metrics = data.get('metrics', list(self.performance_metrics.keys()))
            
            # Calculate date range
            end_date = datetime.now()
            if time_period == 'last_7_days':
                start_date = end_date - timedelta(days=7)
            elif time_period == 'last_30_days':
                start_date = end_date - timedelta(days=30)
            elif time_period == 'last_90_days':
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=30)  # Default to 30 days
            
            # In a real implementation, this would query a database
            # For now, we'll return sample data
            report = {
                "report_period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_candidates": len(self.candidate_pipeline),
                    "hires_made": sum(1 for c in self.candidate_pipeline.values() 
                                     if c["current_stage"] == "Onboarding"),
                    "average_time_to_hire": "25 days"  # Sample data
                },
                "metrics": {}
            }
            
            # Add requested metrics
            for metric in metrics:
                if metric in self.performance_metrics:
                    target = self.performance_metrics[metric]["target"]
                    unit = self.performance_metrics[metric]["unit"]
                    # Simulate some variance around the target
                    current_value = target * (0.9 + 0.2 * (hash(metric) % 100) / 100)
                    report["metrics"][metric] = {
                        "current_value": round(current_value, 2),
                        "target": target,
                        "unit": unit,
                        "status": "meeting" if current_value >= target * 0.9 else "needs_improvement"
                    }
            
            # Add stage-wise analytics
            report["pipeline_analytics"] = {
                stage: sum(1 for c in self.candidate_pipeline.values() 
                          if c["current_stage"] == stage)
                for stage in self.workflow_stages
            }
            
            return json.dumps(report, indent=2)
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return f"Error generating report: {str(e)}"

    def _get_role_description(self) -> str:
        return f"""You are the central coordinator for the hiring process, responsible for managing the entire candidate journey.
        
        Your responsibilities include:
        1. Managing the candidate pipeline through all stages: {', '.join(self.workflow_stages)}
        2. Coordinating between different agents (Screener, Interviewer, Matcher)
        3. Tracking and reporting on key performance metrics
        4. Ensuring a smooth and efficient hiring process
        5. Identifying bottlenecks and areas for improvement
        
        Key Performance Metrics:
        {json.dumps(self.performance_metrics, indent=2)}
        
        Always maintain clear communication and provide timely updates to all stakeholders."""

    def _create_agent(self) -> Any:
        system_message = SystemMessage(content=self.get_system_prompt())
        human_template = """Manage the hiring workflow: {input}
        
        Available actions: next, previous, status, add_note, generate_report
        Example: {{"action": "next", "candidate_id": "123", "current_stage": "Screening"}}"""
        human_message = HumanMessagePromptTemplate.from_template(human_template)
        
        prompt = ChatPromptTemplate.from_messages([
            system_message,
            MessagesPlaceholder(variable_name="chat_history"),
            human_message,
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = initialize_agent(
            self.tools,
            self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            memory=self.memory,
            agent_kwargs={
                'prefix': system_message.content,
                'human_message': human_template,
                'input_variables': ['input', 'chat_history', 'agent_scratchpad']
            }
        )
        
        return agent