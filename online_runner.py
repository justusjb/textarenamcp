import textarena as ta
from agents import get_agent
import time
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('online_runner')

def run_online_game(agent_id='claude-3.7-sonnet-mcp', email="j.beck@startmunich.de", verbose=True, max_retries=10, retry_delay=5):
    """
    Run an online SpellingBee game with a single agent.
    
    Args:
        agent_id: ID of the agent to use
        email: Email address for registration
        verbose: Whether to print game progress
        max_retries: Maximum number of retries for websocket errors
        retry_delay: Delay between retries in seconds
        
    Returns:
        dict: Game rewards
    """
    # Get the agent
    agent, model_name, model_description = get_agent(agent_id)
    
    for attempt in range(max_retries):
        try:
            if verbose and attempt > 0:
                logger.info(f"Retry attempt {attempt}/{max_retries-1}...")
            
            # CRITICAL CHANGE: Get the observation FIRST, then create the environment
            # This way we can generate the action before opening the WebSocket connection
            
            # Create a temporary environment just to get the observation
            temp_env = ta.make_online(
                env_id="SpellingBee-v0",
                model_name=model_name,
                model_description=model_description,
                email=email
            )
            temp_env = ta.wrappers.LLMObservationWrapper(env=temp_env)
            
            # Start the game and get the observation
            temp_env.reset(num_players=1)
            player_id, observation = temp_env.get_observation()
            
            # Close the temporary environment
            try:
                temp_env.close()
            except:
                logger.warning("Error closing temporary environment, continuing anyway")
            
            # Generate the action BEFORE creating the real environment
            # This is the key change - we generate the action while no WebSocket is open
            logger.info("Generating action from agent (this may take some time)...")
            action = agent(observation)
            
            # Extract just the word in brackets
            bracket_pattern = r'\[(.*?)\]'
            matches = re.findall(bracket_pattern, action)
            
            if matches:
                clean_action = f"[{matches[0]}]"
                logger.info(f"Extracted word from response: {clean_action}")
            else:
                clean_action = action
                logger.warning("Could not extract word in brackets from response")
            
            # NOW create the real environment and submit the action immediately
            logger.info("Creating new environment to submit action...")
            env = ta.make_online(
                env_id="SpellingBee-v0",
                model_name=model_name,
                model_description=model_description,
                email=email
            )
            env = ta.wrappers.LLMObservationWrapper(env=env)
            
            # Reset and immediately submit the action
            env.reset(num_players=1)
            
            # Get the new observation (should be the same as before)
            new_player_id, new_observation = env.get_observation()
            
            # Submit the action immediately
            logger.info(f"Submitting action: {clean_action}")
            done, info = env.step(action=clean_action)
            
            # Main game loop for subsequent turns
            while not done:
                try:
                    # Get observation
                    player_id, observation = env.get_observation()
                    
                    # Close this environment
                    try:
                        env.close()
                    except:
                        logger.warning("Error closing environment, continuing anyway")
                    
                    # Generate action offline (no WebSocket open)
                    logger.info("Generating action from agent (this may take some time)...")
                    action = agent(observation)
                    
                    # Extract just the word in brackets
                    matches = re.findall(bracket_pattern, action)
                    
                    if matches:
                        clean_action = f"[{matches[0]}]"
                        logger.info(f"Extracted word from response: {clean_action}")
                    else:
                        clean_action = action
                        logger.warning("Could not extract word in brackets from response")
                    
                    # Create new environment to submit action
                    logger.info("Creating new environment to submit action...")
                    env = ta.make_online(
                        env_id="SpellingBee-v0",
                        model_name=model_name,
                        model_description=model_description,
                        email=email
                    )
                    env = ta.wrappers.LLMObservationWrapper(env=env)
                    
                    # Reset and skip to the current game state
                    env.reset(num_players=1)
                    
                    # Get the new observation (should match the previous one)
                    new_player_id, new_observation = env.get_observation()
                    
                    # Submit the action immediately
                    logger.info(f"Submitting action: {clean_action}")
                    done, info = env.step(action=clean_action)
                    
                except Exception as e:
                    logger.error(f"Error during game step: {str(e)}")
                    if "websocket" in str(e).lower() or "timeout" in str(e).lower() or "connection" in str(e).lower():
                        # Try to recover by waiting a bit and continuing
                        logger.info("Connection issue detected. Waiting before continuing...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise
            
            # Get final rewards
            rewards = env.close()
            if verbose:
                logger.info(f"Game finished with rewards: {rewards}")
            
            return rewards
            
        except Exception as e:
            logger.error(f"Error running online game: {str(e)}")
            
            if "websocket" in str(e).lower() or "timeout" in str(e).lower() or "connection" in str(e).lower():
                if attempt < max_retries - 1:
                    logger.info(f"Connection issue detected. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error("Max retries reached. Could not connect to TextArena server.")
                    return {"error": "connection_failed_after_retries"}
            else:
                # For other types of errors, don't retry
                raise

if __name__ == "__main__":
    # When run directly, use the default agent
    run_online_game()
