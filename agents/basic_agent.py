import os
import textarena as ta
from dotenv import load_dotenv

def create_agent(model_name="anthropic/claude-3.7-sonnet:thinking"):
    """
    Factory function to create a basic Claude agent.
    
    Args:
        model_name: The model to use via OpenRouter
        
    Returns:
        agent: A configured OpenRouterAgent
    """
    # Load environment variables
    load_dotenv()
    
    # Get the OpenRouter API key
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        raise ValueError("Please set the OPENROUTER_API_KEY environment variable in your .env file")
    
    # Set the OpenRouter API key
    os.environ["OPENROUTER_API_KEY"] = openrouter_api_key
    
    return ta.agents.OpenRouterAgent(model_name=model_name)
