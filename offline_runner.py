import textarena as ta
from agents import get_agent

def run_offline_game(agent_id_1='claude-3.7-sonnet-mcp', agent_id_2='claude-3.7-sonnet', verbose=True):
    """
    Run an offline SpellingBee game between two agents.
    
    Args:
        agent_id_1: ID of the first agent
        agent_id_2: ID of the second agent
        verbose: Whether to print game progress
        
    Returns:
        dict: Game rewards
    """
    # Get the agents
    agent_1, model_name_1, _ = get_agent(agent_id_1)
    agent_2, model_name_2, _ = get_agent(agent_id_2)
    
    # Initialize agents
    agents = {
        0: agent_1,
        1: agent_2,
    }
    
    # Initialize environment and wrap it
    env = ta.make(env_id="SpellingBee-v0")
    env = ta.wrappers.LLMObservationWrapper(env=env)
    env = ta.wrappers.SimpleRenderWrapper(
        env=env,
        player_names={0: f"{model_name_1} (Player 0)", 1: f"{model_name_2} (Player 1)"},
    )
    
    # Start the game
    env.reset(num_players=len(agents))
    
    # Main game loop
    done = False
    while not done:
        player_id, observation = env.get_observation()
        action = agents[player_id](observation)
        done, info = env.step(action=action)
    
    # Get final rewards
    rewards = env.close()
    if verbose:
        print(f"Game finished with rewards: {rewards}")
    
    return rewards

if __name__ == "__main__":
    # When run directly, use the MCP agent vs regular Claude
    run_offline_game(agent_id_1='claude-3.7-sonnet-mcp', agent_id_2='claude-3.7-sonnet')
