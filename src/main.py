import os
import sys
from utils.file_utils import load_config
from llm.lm_studio_client import LmStudioClient
from search.interactive import interactive_search

def main():
    # Ensure config directory exists
    config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
    config_path = os.path.join(config_dir, 'settings.yml')
    
    # Load configuration
    config = load_config(config_path)
    
    # Initialize the LLM client
    llm_client = LmStudioClient()
    llm_client.set_model(config.get('llm', {}).get('model_name', 'local-model'))
    
    # Start interactive search
    interactive_search(llm_client, config)

if __name__ == "__main__":
    main()