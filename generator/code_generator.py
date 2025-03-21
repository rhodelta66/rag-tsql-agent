from typing import List, Dict, Any, Optional
import logging
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.chains import LLMChain
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TSQLCodeGenerator:
    """
    Generate T-SQL code for UI-related stored procedures.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the code generator.
        
        Args:
            api_key: OpenAI API key (if None, will look for OPENAI_API_KEY environment variable)
        """
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            
        self.llm = OpenAI(temperature=0.2)
        self.setup_prompts()
        
    def setup_prompts(self):
        """Set up prompt templates for code generation."""
        # Prompt for generating UI procedure
        self.ui_procedure_prompt = PromptTemplate(
            input_variables=["description", "similar_procedures"],
            template="""
            You are an expert T-SQL developer specializing in creating UI-related stored procedures.
            
            Create a T-SQL stored procedure that implements the following UI:
            {description}
            
            Here are some similar procedures for reference:
            
            {similar_procedures}
            
            Follow these guidelines:
            1. Use sp_api_modal_* procedures for UI components
            2. Include proper variable declarations and synchronization
            3. Implement appropriate control flow for button clicks
            4. Add helpful comments explaining the code
            5. Follow best practices for T-SQL UI development
            
            Return only the complete T-SQL code without any additional explanation.
            """
        )
        
        self.ui_procedure_chain = LLMChain(
            llm=self.llm,
            prompt=self.ui_procedure_prompt
        )
        
        # Prompt for modifying existing procedure
        self.modify_procedure_prompt = PromptTemplate(
            input_variables=["original_code", "modification_request"],
            template="""
            You are an expert T-SQL developer specializing in UI-related stored procedures.
            
            Here is an existing T-SQL stored procedure:
            
            {original_code}
            
            Modify this procedure according to the following request:
            {modification_request}
            
            Follow these guidelines:
            1. Maintain the existing structure and variable naming conventions
            2. Only change what is necessary to fulfill the request
            3. Add helpful comments explaining your changes
            4. Ensure all UI components work together correctly
            
            Return only the complete modified T-SQL code without any additional explanation.
            """
        )
        
        self.modify_procedure_chain = LLMChain(
            llm=self.llm,
            prompt=self.modify_procedure_prompt
        )
    
    def generate_ui_procedure(self, description: str, similar_procedures: List[Dict[str, Any]]) -> str:
        """
        Generate a new UI-related stored procedure.
        
        Args:
            description: Description of what the procedure should do
            similar_procedures: List of similar procedures for reference
            
        Returns:
            Generated T-SQL code
        """
        # Format similar procedures as text
        similar_procs_text = ""
        for i, proc in enumerate(similar_procedures):
            similar_procs_text += f"--- PROCEDURE {i+1}: {proc['name']} ---\n"
            similar_procs_text += proc['text']
            similar_procs_text += "\n\n"
            
        # Generate code
        try:
            result = self.ui_procedure_chain.run(
                description=description,
                similar_procedures=similar_procs_text
            )
            
            logger.info(f"Generated UI procedure code ({len(result)} characters)")
            return result
            
        except Exception as e:
            logger.error(f"Error generating UI procedure: {str(e)}")
            return f"Error generating code: {str(e)}"
    
    def modify_procedure(self, original_code: str, modification_request: str) -> str:
        """
        Modify an existing stored procedure.
        
        Args:
            original_code: Original T-SQL code
            modification_request: Description of the requested modifications
            
        Returns:
            Modified T-SQL code
        """
        try:
            result = self.modify_procedure_chain.run(
                original_code=original_code,
                modification_request=modification_request
            )
            
            logger.info(f"Modified procedure code ({len(result)} characters)")
            return result
            
        except Exception as e:
            logger.error(f"Error modifying procedure: {str(e)}")
            return f"Error modifying code: {str(e)}"
