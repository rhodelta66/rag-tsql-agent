import pyodbc
import sqlalchemy as sa
from sqlalchemy import create_engine, text
import os
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLServerConnector:
    """
    Connector for SQL Server Express with Windows authentication,
    specialized for retrieving UI-related stored procedures.
    """
    
    def __init__(self, server: str, database: str):
        """
        Initialize the SQL Server connector.
        
        Args:
            server: SQL Server instance name
            database: Database name
        """
        self.server = server
        self.database = database
        self.connection_string = f"Driver={{SQL Server}};Server={server};Database={database};Trusted_Connection=yes;"
        self.engine = None
        
    def connect(self) -> bool:
        """
        Establish connection to the SQL Server database.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.engine = create_engine(f"mssql+pyodbc:///?odbc_connect={self.connection_string}")
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info(f"Successfully connected to {self.server}/{self.database}")
                return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            return False
    
    def get_stored_procedures(self, filter_ui_only: bool = False) -> List[Dict[str, Any]]:
        """
        Retrieve stored procedures from the database.
        
        Args:
            filter_ui_only: If True, only return UI-related stored procedures
            
        Returns:
            List of dictionaries containing stored procedure information
        """
        if not self.engine:
            logger.error("Not connected to database. Call connect() first.")
            return []
            
        try:
            query = """
            SELECT 
                ROUTINE_SCHEMA as schema_name,
                ROUTINE_NAME as procedure_name,
                CREATED as created_date,
                LAST_ALTERED as modified_date
            FROM 
                INFORMATION_SCHEMA.ROUTINES
            WHERE 
                ROUTINE_TYPE = 'PROCEDURE'
            """
            
            if filter_ui_only:
                # Filter for UI-related stored procedures (those that use sp_api_* procedures)
                query = """
                SELECT DISTINCT
                    r.ROUTINE_SCHEMA as schema_name,
                    r.ROUTINE_NAME as procedure_name,
                    r.CREATED as created_date,
                    r.LAST_ALTERED as modified_date
                FROM 
                    INFORMATION_SCHEMA.ROUTINES r
                WHERE 
                    r.ROUTINE_TYPE = 'PROCEDURE'
                    AND (
                        OBJECT_DEFINITION(OBJECT_ID(r.ROUTINE_SCHEMA + '.' + r.ROUTINE_NAME)) LIKE '%sp_api_%'
                        OR OBJECT_DEFINITION(OBJECT_ID(r.ROUTINE_SCHEMA + '.' + r.ROUTINE_NAME)) LIKE '%modal%'
                    )
                """
                
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                procedures = [dict(row) for row in result]
                logger.info(f"Retrieved {len(procedures)} stored procedures")
                return procedures
                
        except Exception as e:
            logger.error(f"Error retrieving stored procedures: {str(e)}")
            return []

    def get_procedure_definition(self, schema_name: str, procedure_name: str) -> Optional[str]:
        """
        Get the T-SQL definition of a stored procedure.
        
        Args:
            schema_name: Schema name of the procedure
            procedure_name: Name of the procedure
            
        Returns:
            String containing the procedure definition or None if not found
        """
        if not self.engine:
            logger.error("Not connected to database. Call connect() first.")
            return None
            
        try:
            query = f"""
            SELECT OBJECT_DEFINITION(OBJECT_ID('{schema_name}.{procedure_name}')) as definition
            """
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                row = result.fetchone()
                if row and row[0]:
                    return row[0]
                else:
                    logger.warning(f"No definition found for {schema_name}.{procedure_name}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error retrieving procedure definition: {str(e)}")
            return None
    
    def get_procedure_parameters(self, schema_name: str, procedure_name: str) -> List[Dict[str, Any]]:
        """
        Get the parameters of a stored procedure.
        
        Args:
            schema_name: Schema name of the procedure
            procedure_name: Name of the procedure
            
        Returns:
            List of dictionaries containing parameter information
        """
        if not self.engine:
            logger.error("Not connected to database. Call connect() first.")
            return []
            
        try:
            query = f"""
            SELECT 
                p.name as parameter_name,
                t.name as data_type,
                p.max_length,
                p.is_output
            FROM 
                sys.parameters p
                INNER JOIN sys.types t ON p.system_type_id = t.system_type_id
                INNER JOIN sys.procedures sp ON p.object_id = sp.object_id
                INNER JOIN sys.schemas s ON sp.schema_id = s.schema_id
            WHERE 
                s.name = '{schema_name}' AND sp.name = '{procedure_name}'
            """
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                parameters = [dict(row) for row in result]
                logger.info(f"Retrieved {len(parameters)} parameters for {schema_name}.{procedure_name}")
                return parameters
                
        except Exception as e:
            logger.error(f"Error retrieving procedure parameters: {str(e)}")
            return []
    
    def get_ui_components(self, procedure_definition: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract UI components from a procedure definition.
        
        Args:
            procedure_definition: T-SQL definition of the procedure
            
        Returns:
            Dictionary with UI component types as keys and lists of components as values
        """
        if not procedure_definition:
            return {}
            
        components = {
            "modal_text": [],
            "modal_input": [],
            "modal_button": [],
            "toast": [],
            "other": []
        }
        
        # Extract sp_api_modal_text components
        import re
        
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
