import os
import yaml
import json

def load_config(config_path):
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration values
    """
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Config file not found at {config_path}")
        return create_default_config(config_path)
        
def create_default_config(config_path):
    """
    Create a default configuration file.
    
    Args:
        config_path: Path where the configuration file should be created
        
    Returns:
        Dictionary containing default configuration values
    """
    config = {
        'llm': {
            'provider': 'lm_studio',
            'model_name': 'local-model',
            'temperature': 0.7,
            'max_tokens': 2048
        },
        'search': {
            'default_iterations': 2,
            'max_iterations': 5,
            'results_per_search': 5,
            'content_fetch_limit': 3
        },
        'paths': {
            'results_dir': 'results'
        }
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    # Write default config
    try:
        with open(config_path, 'w') as file:
            yaml.dump(config, file, default_flow_style=False)
        print(f"Created default configuration at {config_path}")
    except Exception as e:
        print(f"Error creating default configuration: {e}")
    
    return config

def save_search_results(results_dir, data):
    """
    Save search results to a JSON file.
    
    Args:
        results_dir: Directory where results should be saved
        data: Dictionary containing search results data
        
    Returns:
        Path to the saved file or None if an error occurred
    """
    try:
        os.makedirs(results_dir, exist_ok=True)
        
        filename = f"search_{data.get('timestamp', 'results')}.json"
        filepath = os.path.join(results_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return filepath
    except Exception as e:
        print(f"Error saving results: {e}")
        return None