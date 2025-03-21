import re
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StoredProcedureAnalyzer:
    """
    Analyzer for T-SQL stored procedures, specialized for UI-related procedures.
    """
    
    def __init__(self):
        """Initialize the stored procedure analyzer."""
        pass
    
    def analyze_procedure(self, procedure_definition: str) -> Dict[str, Any]:
        """
        Analyze a stored procedure definition and extract metadata.
        
        Args:
            procedure_definition: T-SQL definition of the procedure
            
        Returns:
            Dictionary containing extracted metadata
        """
        if not procedure_definition:
            return {}
            
        metadata = {
            "variables": self._extract_variables(procedure_definition),
            "ui_components": self._extract_ui_components(procedure_definition),
            "control_flow": self._extract_control_flow(procedure_definition),
            "api_calls": self._extract_api_calls(procedure_definition),
            "summary": self._generate_summary(procedure_definition)
        }
        
        return metadata
    
    def _extract_variables(self, procedure_definition: str) -> List[Dict[str, str]]:
        """Extract variable declarations from the procedure."""
        variables = []
        
        # Match DECLARE statements
        pattern = r"DECLARE\s+(@\w+)\s+([^;]+)(?:;|$)"
        for match in re.finditer(pattern, procedure_definition, re.IGNORECASE):
            var_name = match.group(1)
            var_type = match.group(2).strip()
            variables.append({
                "name": var_name,
                "type": var_type
            })
            
        return variables
    
    def _extract_ui_components(self, procedure_definition: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract UI components from the procedure."""
        components = {
            "modal_text": [],
            "modal_input": [],
            "modal_button": [],
            "toast": [],
            "other": []
        }
        
        # Modal text components
        text_pattern = r"EXEC\s+sp_api_modal_text\s+@text\s*=\s*N?'([^']+)'(?:.*?@class\s*=\s*N?'([^']+)')?"
        for match in re.finditer(text_pattern, procedure_definition, re.IGNORECASE):
            components["modal_text"].append({
                "text": match.group(1),
                "class": match.group(2) if match.group(2) else ""
            })
        
        # Modal input components
        input_pattern = r"EXEC\s+sp_api_modal_input\s+@name\s*=\s*N?'([^']+)'(?:.*?@value\s*=\s*([^,\s]+))?(?:.*?@placeholder\s*=\s*N?'([^']+)')?"
        for match in re.finditer(input_pattern, procedure_definition, re.IGNORECASE):
            components["modal_input"].append({
                "name": match.group(1),
                "value_var": match.group(2) if match.group(2) else "",
                "placeholder": match.group(3) if match.group(3) else ""
            })
        
        # Modal button components
        button_pattern = r"EXEC\s+sp_api_modal_button\s+@name\s*=\s*N?'([^']+)'(?:.*?@value\s*=\s*N?'([^']+)')?(?:.*?@class\s*=\s*N?'([^']+)')?"
        for match in re.finditer(button_pattern, procedure_definition, re.IGNORECASE):
            components["modal_button"].append({
                "name": match.group(1),
                "value": match.group(2) if match.group(2) else "",
                "class": match.group(3) if match.group(3) else ""
            })
        
        # Toast notifications
        toast_pattern = r"EXEC\s+sp_api_toast\s+@text\s*=\s*N?'([^']+)'(?:.*?@class\s*=\s*N?'([^']+)')?(?:.*?@seconds\s*=\s*(\d+))?"
        for match in re.finditer(toast_pattern, procedure_definition, re.IGNORECASE):
            components["toast"].append({
                "text": match.group(1),
                "class": match.group(2) if match.group(2) else "",
                "seconds": match.group(3) if match.group(3) else "3"
            })
        
        return components
    
    def _extract_control_flow(self, procedure_definition: str) -> List[Dict[str, Any]]:
        """Extract control flow structures from the procedure."""
        control_flow = []
        
        # IF statements
        if_pattern = r"IF\s+(.+?)\s+BEGIN\s+(.+?)\s+END"
        for match in re.finditer(if_pattern, procedure_definition, re.IGNORECASE | re.DOTALL):
            condition = match.group(1).strip()
            body = match.group(2).strip()
            control_flow.append({
                "type": "if",
                "condition": condition,
                "body_length": len(body)
            })
        
        # WHILE loops
        while_pattern = r"WHILE\s+(.+?)\s+BEGIN\s+(.+?)\s+END"
        for match in re.finditer(while_pattern, procedure_definition, re.IGNORECASE | re.DOTALL):
            condition = match.group(1).strip()
            body = match.group(2).strip()
            control_flow.append({
                "type": "while",
                "condition": condition,
                "body_length": len(body)
            })
            
        return control_flow
    
    def _extract_api_calls(self, procedure_definition: str) -> List[str]:
        """Extract API calls from the procedure."""
        api_calls = []
        
        # Match EXEC sp_api_* calls
        pattern = r"EXEC\s+(sp_api_\w+)"
        for match in re.finditer(pattern, procedure_definition, re.IGNORECASE):
            api_call = match.group(1)
            if api_call not in api_calls:
                api_calls.append(api_call)
            
        return api_calls
    
    def _generate_summary(self, procedure_definition: str) -> str:
        """Generate a summary of the procedure."""
        # Count UI components
        ui_components = self._extract_ui_components(procedure_definition)
        total_components = sum(len(components) for components in ui_components.values())
        
        # Count variables
        variables = self._extract_variables(procedure_definition)
        
        # Count control flow structures
        control_flow = self._extract_control_flow(procedure_definition)
        
        # Generate summary
        summary = f"UI procedure with {total_components} UI components, {len(variables)} variables, and {len(control_flow)} control flow structures."
        
        return summary
