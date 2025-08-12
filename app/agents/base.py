from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from langchain.agents import AgentExecutor, AgentType, initialize_agent, Tool
from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryMemory
from langchain.tools import BaseTool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder
)
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from app.core.config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
        role: str,
        tools: List[Union[BaseTool, Tool]],
        temperature: float = 0.7,
        model_name: str = "gpt-4-turbo-preview",
        max_memory_items: int = 20
    ):
        self.name = name
        self.role = role
        self.tools = tools
        self.temperature = temperature
        self.model_name = model_name
        
        # Initialize LLM with streaming support
        self.llm = ChatOpenAI(
            temperature=temperature,
            model_name=model_name,
            streaming=True,
            callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
            request_timeout=60
        )
        
        # Enhanced memory with conversation summary
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=max_memory_items,
            output_key="output"
        )
        
        # Additional memory for long-term context
        self.summary_memory = ConversationSummaryMemory(
            llm=ChatOpenAI(temperature=0.3),
            memory_key="summary_memory",
            return_messages=True
        )
        
        # Initialize conversation context
        self.context = {
            "current_task": None,
            "user_preferences": {},
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Create the agent
        self.agent = self._create_agent()
        
        logger.info(f"Initialized {self.name} agent with {len(tools)} tools")

    @abstractmethod
    def _get_role_description(self) -> str:
        """Return a detailed description of the agent's role and responsibilities."""
        pass

    @abstractmethod
    def _create_agent(self) -> Any:
        """Create and return the LangChain agent instance."""
        pass

    def get_system_prompt(self) -> str:
        """Generate the system prompt for the agent."""
        current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        return f"""You are {self.name}, an AI agent specialized in {self.role}.
        
        {self._get_role_description()}
        
        Current Date and Time: {current_time}
        
        Guidelines:
        1. Be professional, empathetic, and concise
        2. Always maintain context of the conversation
        3. Ask clarifying questions when information is unclear
        4. Provide structured, actionable responses
        5. Use markdown formatting for better readability
        6. When providing code, use appropriate syntax highlighting
        7. Always consider the user's context and preferences
        8. Be proactive in suggesting next steps
        
        Available Tools:
        {', '.join([tool.name for tool in self.tools])}
        
        Current Task: {self.context.get('current_task', 'None')}
        
        User Preferences: {str(self.context.get('user_preferences', {}))}"""

    def run(self, input_text: str, **kwargs) -> str:
        """Run the agent with the given input and optional context."""
        try:
            # Update context with any provided kwargs
            self._update_context(**kwargs)
            
            # Create the prompt with context
            prompt = self._create_prompt(input_text)
            
            # Run the agent
            response = self.agent.run(
                {
                    "input": input_text,
                    "context": self.context,
                    **kwargs
                },
                callbacks=[],
                include_run_info=True
            )
            
            # Update conversation summary
            self._update_conversation_summary(input_text, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in {self.name} agent: {str(e)}", exc_info=True)
            return f"I encountered an error while processing your request. Please try again later. Error: {str(e)}"
            
    def _create_prompt(self, input_text: str) -> dict:
        """Create a structured prompt with conversation history and context."""
        messages = [
            SystemMessage(content=self.get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessage(content=input_text)
        ]
        return {"messages": messages}
        
    def _update_context(self, **kwargs) -> None:
        """Update the agent's context with new information."""
        if 'current_task' in kwargs:
            self.context['current_task'] = kwargs['current_task']
        if 'user_preferences' in kwargs:
            self.context['user_preferences'].update(kwargs['user_preferences'])
        self.context['last_updated'] = datetime.utcnow().isoformat()
        
    def _update_conversation_summary(self, input_text: str, response: str) -> None:
        """Update the conversation summary with the latest exchange."""
        self.summary_memory.save_context(
            {"input": input_text},
            {"output": response}
        )

    def clear_memory(self):
        """Clear the agent's conversation memory."""
        self.memory.clear()

    async def get_memory(self) -> Dict[str, Any]:
        """Get the agent's memory state."""
        try:
            return {
                "chat_history": self.memory.chat_memory.messages,
                "summary": self.summary_memory.buffer,
                "context": self.context,
                "variables": self.memory.variables
            }
        except Exception as e:
            logger.error(f"Error getting memory: {str(e)}")
            return {"error": "Failed to retrieve memory"}

    async def clear_memory(self) -> None:
        """Clear the agent's memory and reset context."""
        try:
            self.memory.clear()
            self.summary_memory.clear()
            self.context = {
                "current_task": None,
                "user_preferences": {},
                "last_updated": datetime.utcnow().isoformat()
            }
            logger.info(f"{self.name} agent memory cleared")
        except Exception as e:
            logger.error(f"Error clearing memory: {str(e)}")
            raise