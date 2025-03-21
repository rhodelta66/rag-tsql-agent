import os
import sys
import logging
from ui.cli import TSQLCLI

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the application."""
    cli = TSQLCLI()
    cli.run()

if __name__ == "__main__":
    main()
