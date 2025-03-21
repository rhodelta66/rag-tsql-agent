import argparse
import logging
import os
import sys
from typing import Dict, Any, List, Optional
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connector import SQLServerConnector
from analyzer.procedure_analyzer import StoredProcedureAnalyzer
from rag.embeddings import ProcedureEmbeddings
from rag.retriever import ProcedureRetriever
from generator.code_generator import TSQLCodeGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TSQLCLI:
    """
    Command-line interface for the T-SQL RAG agent.
    """
    
    def __init__(self):
        """Initialize the CLI."""
        self.config = self._load_config()
        self.db_connector = None
        self.analyzer = StoredProcedureAnalyzer()
        self.embeddings = ProcedureEmbeddings()
        self.retriever = None
        self.generator = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or environment variables."""
        config = {
            "server": os.environ.get("SQL_SERVER", "localhost\\SQLEXPRESS"),
            "database": os.environ.get("SQL_DATABASE", "master"),
            "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
            "data_dir": os.environ.get("DATA_DIR", "data")
        }
        
        # Try to load from config file
        config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                logger.warning(f"Error loading config file: {str(e)}")
                
        return config
    
    def _save_config(self) -> bool:
        """Save configuration to file."""
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
        os.makedirs(config_dir, exist_ok=True)
        
        config_file = os.path.join(config_dir, "config.json")
        try:
            with open(config_file, "w") as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving config file: {str(e)}")
            return False
    
    def setup(self) -> bool:
        """Set up the CLI components."""
        # Create data directory
        os.makedirs(self.config["data_dir"], exist_ok=True)
        
        # Initialize database connector
        self.db_connector = SQLServerConnector(
            server=self.config["server"],
            database=self.config["database"]
        )
        
        # Initialize retriever
        self.retriever = ProcedureRetriever(self.embeddings)
        
        # Initialize generator
        self.generator = TSQLCodeGenerator(api_key=self.config["openai_api_key"])
        
        return True
    
    def connect_to_database(self) -> bool:
        """Connect to the database."""
        if not self.db_connector:
            logger.error("Database connector not initialized")
            return False
            
        return self.db_connector.connect()
    
    def index_procedures(self, filter_ui_only: bool = True) -> bool:
        """
        Index stored procedures from the database.
        
        Args:
            filter_ui_only: If True, only index UI-related procedures
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db_connector:
            logger.error("Database connector not initialized")
            return False
            
        # Get procedures
        procedures = self.db_connector.get_stored_procedures(filter_ui_only=filter_ui_only)
        if not procedures:
            logger.warning("No procedures found")
            return False
            
        logger.info(f"Indexing {len(procedures)} procedures")
        
        # Process each procedure
        for proc in procedures:
            # Get procedure definition
            definition = self.db_connector.get_procedure_definition(
                proc["schema_name"],
                proc["procedure_name"]
            )
            
            if not definition:
                logger.warning(f"No definition found for {proc['schema_name']}.{proc['procedure_name']}")
                continue
                
            # Analyze procedure
            metadata = self.analyzer.analyze_procedure(definition)
            
            # Add to index
            proc_id = f"{proc['schema_name']}.{proc['procedure_name']}"
            proc_name = proc["procedure_name"]
            self.embeddings.add_procedure(proc_id, proc_name, definition, metadata)
            
        # Save index
        index_dir = os.path.join(self.config["data_dir"], "index")
        self.embeddings.save(index_dir)
        
        logger.info(f"Indexed {len(procedures)} procedures")
        return True
    
    def load_index(self) -> bool:
        """Load the procedure index from disk."""
        index_dir = os.path.join(self.config["data_dir"], "index")
        return self.embeddings.load(index_dir)
    
    def generate_code(self, description: str, k: int = 3) -> str:
        """
        Generate T-SQL code based on a description.
        
        Args:
            description: Description of what the procedure should do
            k: Number of similar procedures to use as reference
            
        Returns:
            Generated T-SQL code
        """
        if not self.retriever or not self.generator:
            logger.error("Retriever or generator not initialized")
            return "Error: System not fully initialized"
            
        # Retrieve similar procedures
        similar_procedures = self.retriever.retrieve(description, k)
        
        # Generate code
        code = self.generator.generate_ui_procedure(description, similar_procedures)
        
        return code
    
    def modify_code(self, procedure_name: str, modification_request: str) -> str:
        """
        Modify an existing procedure.
        
        Args:
            procedure_name: Name of the procedure to modify
            modification_request: Description of the requested modifications
            
        Returns:
            Modified T-SQL code
        """
        if not self.db_connector or not self.generator:
            logger.error("Database connector or generator not initialized")
            return "Error: System not fully initialized"
            
        # Find the procedure
        schema_name = "dbo"  # Default schema
        if "." in procedure_name:
            parts = procedure_name.split(".")
            schema_name = parts[0]
            procedure_name = parts[1]
            
        # Get procedure definition
        definition = self.db_connector.get_procedure_definition(schema_name, procedure_name)
        if not definition:
            return f"Error: Procedure {schema_name}.{procedure_name} not found"
            
        # Modify code
        modified_code = self.generator.modify_procedure(definition, modification_request)
        
        return modified_code
    
    def run(self):
        """Run the CLI."""
        parser = argparse.ArgumentParser(description="T-SQL RAG Agent CLI")
        subparsers = parser.add_subparsers(dest="command", help="Command to run")
        
        # Setup command
        setup_parser = subparsers.add_parser("setup", help="Set up the agent")
        setup_parser.add_argument("--server", help="SQL Server instance name")
        setup_parser.add_argument("--database", help="Database name")
        setup_parser.add_argument("--api-key", help="OpenAI API key")
        
        # Index command
        index_parser = subparsers.add_parser("index", help="Index stored procedures")
        index_parser.add_argument("--all", action="store_true", help="Index all procedures, not just UI-related ones")
        
        # Generate command
        generate_parser = subparsers.add_parser("generate", help="Generate T-SQL code")
        generate_parser.add_argument("description", help="Description of what the procedure should do")
        generate_parser.add_argument("--output", help="Output file path")
        generate_parser.add_argument("--similar", type=int, default=3, help="Number of similar procedures to use")
        
        # Modify command
        modify_parser = subparsers.add_parser("modify", help="Modify an existing procedure")
        modify_parser.add_argument("procedure", help="Name of the procedure to modify")
        modify_parser.add_argument("request", help="Description of the requested modifications")
        modify_parser.add_argument("--output", help="Output file path")
        
        # Parse arguments
        args = parser.parse_args()
        
        # Handle commands
        if args.command == "setup":
            # Update config
            if args.server:
                self.config["server"] = args.server
            if args.database:
                self.config["database"] = args.database
            if args.api_key:
                self.config["openai_api_key"] = args.api_key
                
            # Save config
            self._save_config()
            
            # Set up components
            if self.setup():
                print("Setup completed successfully")
            else:
                print("Setup failed")
                
        elif args.command == "index":
            # Set up components
            if not self.setup():
                print("Setup failed")
                return
                
            # Connect to database
            if not self.connect_to_database():
                print("Failed to connect to database")
                return
                
            # Index procedures
            if self.index_procedures(filter_ui_only=not args.all):
                print("Indexing completed successfully")
            else:
                print("Indexing failed")
                
        elif args.command == "generate":
            # Set up components
            if not self.setup():
                print("Setup failed")
                return
                
            # Load index
            if not self.load_index():
                print("Failed to load index")
                return
                
            # Generate code
            code = self.generate_code(args.description, args.similar)
            
            # Output code
            if args.output:
                try:
                    with open(args.output, "w") as f:
                        f.write(code)
                    print(f"Code written to {args.output}")
                except Exception as e:
                    print(f"Error writing to file: {str(e)}")
                    print(code)
            else:
                print(code)
                
        elif args.command == "modify":
            # Set up components
            if not self.setup():
                print("Setup failed")
                return
                
            # Connect to database
            if not self.connect_to_database():
                print("Failed to connect to database")
                return
                
            # Modify code
            code = self.modify_code(args.procedure, args.request)
            
            # Output code
            if args.output:
                try:
                    with open(args.output, "w") as f:
                        f.write(code)
                    print(f"Code written to {args.output}")
                except Exception as e:
                    print(f"Error writing to file: {str(e)}")
                    print(code)
            else:
                print(code)
                
        else:
            parser.print_help()
