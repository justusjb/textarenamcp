"""
Specific agent configurations for SpellingBee.
Each agent has a predefined model_name, model_description, and agent implementation.
"""
import threading
import time
import sys
import os

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .basic_agent import create_agent
from .mcp_agent import create_dictionary_agent
import mcp_server

# Dictionary of available specific agents
SPECIFIC_AGENTS = {}

def register_agent(agent_id, create_fn, model_name, model_description):
    """
    Register a specific agent configuration.
    
    Args:
        agent_id: Unique identifier for the agent
        create_fn: Function to create the agent
        model_name: Name of the model for online competition
        model_description: Description of the model for online competition
    """
    SPECIFIC_AGENTS[agent_id] = {
        'create_fn': create_fn,
        'model_name': model_name,
        'model_description': model_description
    }

# Register basic Claude 3.7 Sonnet agent
register_agent(
    agent_id='claude-3.7-sonnet',
    create_fn=lambda: create_agent(model_name="anthropic/claude-3.7-sonnet:thinking"),
    model_name="Claude-3.7-Sonnet-thinking",
    model_description="Anthropic's Claude 3.7 Sonnet model for SpellingBee"
)

# Register Amazon Nova Lite agent
register_agent(
    agent_id='nova-lite',
    create_fn=lambda: create_agent(model_name="amazon/nova-lite-v1"),
    model_name="Amazon-Nova-Lite",
    model_description="Amazon's Nova Lite v1 model for SpellingBee"
)
# anthropic/claude-3.5-haiku
register_agent(
    agent_id='claude-3.5-haiku',
    create_fn=lambda: create_agent(model_name="anthropic/claude-3.5-haiku"),
    model_name="Claude-3.5-Haiku",
    model_description="Anthropic's Claude 3.5 Haiku model for SpellingBee"
)

# MCP server singleton
_mcp_server_thread = None
_mcp_port = 8000

def _ensure_mcp_server():
    """Ensure the MCP server is running."""
    global _mcp_server_thread
    if _mcp_server_thread is None:
        print("Starting MCP server...")
        _mcp_server_thread = mcp_server.start_server_thread(port=_mcp_port)
        time.sleep(2)  # Give the server a moment to start up
        print("MCP server started")

# Register MCP-enhanced Claude 3.7 Sonnet agent
register_agent(
    agent_id='claude-3.7-sonnet-mcp',
    create_fn=lambda: create_dictionary_agent(
        model_name="anthropic/claude-3.7-sonnet"
    ),
    model_name="Skill-issue-v18",
    model_description="Claude 3.7 Sonnet with dictionary-based word finding"
)

# Register MCP-enhanced Nova Lite agent
register_agent(
    agent_id='nova-lite-mcp',
    create_fn=lambda: (_ensure_mcp_server(), create_mcp_agent(
        model_name="amazon/nova-lite-v1",
        mcp_server_url=f"http://localhost:{_mcp_port}"
    ))[1],
    model_name="Amazon-Nova-Lite-MCP-Enhanced",
    model_description="Amazon's Nova Lite v1 model enhanced with MCP word-finding capabilities"
)
# Register MCP-enhanced Claude 3.5 Haiku agent
register_agent(
    agent_id='claude-3.5-haiku-mcp',
    create_fn=lambda: (_ensure_mcp_server(), create_mcp_agent(
        model_name="anthropic/claude-3.5-haiku",
        mcp_server_url=f"http://localhost:{_mcp_port}"
    ))[1],
    model_name="Claude-3.5-Haiku-MCP-Enhanced",
    model_description="Anthropic's Claude 3.5 Haiku model enhanced with MCP word-finding capabilities"
)

def get_agent(agent_id):
    """
    Get a specific agent by ID.
    
    Args:
        agent_id: ID of the agent to get
        
    Returns:
        tuple: (agent_function, model_name, model_description)
    """
    if agent_id not in SPECIFIC_AGENTS:
        raise ValueError(f"Unknown agent ID: {agent_id}. Available agents: {list(SPECIFIC_AGENTS.keys())}")
    
    agent_config = SPECIFIC_AGENTS[agent_id]
    agent = agent_config['create_fn']()
    return agent, agent_config['model_name'], agent_config['model_description']

def list_agents():
    """List all available specific agents."""
    return list(SPECIFIC_AGENTS.keys())
