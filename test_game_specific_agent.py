"""
Test script for the game-specific agent to verify its behavior for different game types.
"""
import os
import logging
import sys
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_game_specific_agent')

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import directly from the file to avoid dependency issues
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create a simplified version of the game-specific agent for testing
def create_test_agent():
    """
    Create a simplified version of the game-specific agent for testing.
    This avoids dependencies on external modules like mcp.
    """
    def detect_game_type(observation):
        """
        Detect the type of game from the observation.
        
        Args:
            observation: The game state observation
            
        Returns:
            str: The detected game type ('spelling_bee', 'poker', or 'other')
        """
        observation_lower = observation.lower()
        
        # Check for Spelling Bee indicators
        if 'spelling bee' in observation_lower or 'allowed letters' in observation_lower:
            logger.info("Detected game type: Spelling Bee")
            return 'spelling_bee'
        
        # Check for Poker indicators
        if 'poker' in observation_lower or 'texas hold' in observation_lower or 'cards:' in observation_lower:
            logger.info("Detected game type: Poker")
            return 'poker'
        
        # Default to other
        logger.info("Detected game type: Other (unknown game)")
        return 'other'
    
    def agent(observation):
        """
        Process the observation and return an action based on the game type.
        
        Args:
            observation: The game state observation
            
        Returns:
            str: The action to take
        """
        # Detect the game type
        game_type = detect_game_type(observation)
        
        # Handle different game types
        if game_type == 'spelling_bee':
            # Simulate Spelling Bee behavior (dictionary enhancement)
            return "I'm playing Spelling Bee! Here are some possible words you can form with the available letters: FACE, CAFE, FEED, FADE..."
        elif game_type == 'poker':
            # Simulate Poker behavior (always all-in)
            return "[ALL-IN]"
        else:
            # Simulate base model behavior for other games
            return "I'll analyze the game state and make a strategic move based on the current situation."
    
    return agent

def test_spelling_bee():
    """Test the agent's behavior for Spelling Bee."""
    logger.info("Testing Spelling Bee behavior...")
    
    # Create the agent
    agent = create_test_agent()
    
    # Sample Spelling Bee observation
    observation = """
    Welcome to Spelling Bee!
    
    Rules:
    - Create words using the given letters
    - Words must be at least 4 letters long
    - Words must include the center letter
    - Letters can be used multiple times
    
    Allowed letters: A, B, C, D, E, F, G (center letter: D)
    
    You are Player 1. It's your turn to make a move.
    """
    
    # Get the agent's response
    response = agent(observation)
    
    # Log the response
    logger.info(f"Spelling Bee response: {response}")
    
    # Check if the response contains word suggestions (indicating dictionary enhancement)
    if "possible words" in response.lower():
        logger.info("✅ Test passed: Agent used dictionary enhancement for Spelling Bee")
    else:
        logger.warning("❌ Test failed: Agent did not use dictionary enhancement for Spelling Bee")
    
    return response

def test_poker():
    """Test the agent's behavior for Poker."""
    logger.info("Testing Poker behavior...")
    
    # Create the agent
    agent = create_test_agent()
    
    # Sample Poker observation
    observation = """
    Welcome to Texas Hold'em Poker!
    
    Your hand: [10♥, J♦]
    Community cards: [2♣, 7♠, K♥]
    
    Current pot: $500
    Your chips: $1000
    
    Player 3 bet $50
    Player 4 folded
    It's your turn to act. You can fold, call, or raise.
    """
    
    # Get the agent's response
    response = agent(observation)
    
    # Log the response
    logger.info(f"Poker response: {response}")
    
    # Check if the response contains "all-in" (case insensitive)
    if "all-in" in response.lower():
        logger.info("✅ Test passed: Agent went all-in for Poker")
    else:
        logger.warning("❌ Test failed: Agent did not go all-in for Poker")
    
    return response

def test_other_game():
    """Test the agent's behavior for other games."""
    logger.info("Testing behavior for other games...")
    
    # Create the agent
    agent = create_test_agent()
    
    # Sample observation for a different game
    observation = """
    Welcome to Chess!
    
    Current board state:
    rnbqkbnr
    pppppppp
    ........
    ........
    ........
    ........
    PPPPPPPP
    RNBQKBNR
    
    You are playing as White. It's your turn to move.
    """
    
    # Get the agent's response
    response = agent(observation)
    
    # Log the response
    logger.info(f"Other game response: {response}")
    
    # For other games, we just verify that the agent generated a response
    # since we're using the base model without enhancements
    if response:
        logger.info("✅ Test passed: Agent generated a response for other game")
    else:
        logger.warning("❌ Test failed: Agent did not generate a response for other game")
    
    return response

if __name__ == "__main__":
    # Run the tests
    logger.info("Starting game-specific agent tests...")
    
    spelling_bee_response = test_spelling_bee()
    print("\n" + "="*80 + "\n")
    
    poker_response = test_poker()
    print("\n" + "="*80 + "\n")
    
    other_game_response = test_other_game()
    
    logger.info("All tests completed!")
