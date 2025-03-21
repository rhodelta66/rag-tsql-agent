import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for the application."""
    
    def __init__(self, config_file: str = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
            "config.json"
        )
        self.config = self._load_config()
        
    def _load_config(self):
        """Load configuration from file or defaults."""
        config = {
            "server": os.environ.get("SQL_SERVER", "localhost\\SQLEXPRESS"),
            "database": os.environ.get("SQL_DATABASE", "master"),
            "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
            "data_dir": os.environ.get("DATA_DIR", "data")
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                logger.warning(f"Error loading config file: {str(e)}")
                
        return config
        
    def save(self):
        """Save configuration to file."""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving config file: {str(e)}")
            return False
            
    def get(self, key, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)
        
    def set(self, key, value):
        """Set a configuration value."""
        self.config[key] = value
