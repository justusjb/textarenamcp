"""
Game-specific agent that adapts behavior based on the detected game type.
"""
import os
import re
import json
import logging
import textarena as ta
from dotenv import load_dotenv

# Import the dictionary module for Spelling Bee
from dictionary import dictionary, EnglishDictionary

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger('game_specific_agent')
logger.setLevel(logging.DEBUG)

# Add a console handler to make sure logs are displayed
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Import the existing functions from mcp_agent.py
from .mcp_agent import extract_letters, find_words_with_dictionary, get_word_length_distribution

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

def create_game_specific_agent(model_name="anthropic/claude-3.7-sonnet"):
    """
    Create an agent that adapts its behavior based on the detected game type.
    
    Args:
        model_name: The model to use via OpenRouter
        
    Returns:
        A function that processes observations and returns actions
    """
    # Load environment variables
    load_dotenv()
    logger.info("Loading environment variables")
    
    # Get the OpenRouter API key
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        raise ValueError("Please set the OPENROUTER_API_KEY environment variable in your .env file")
    
    # Set the OpenRouter API key
    os.environ["OPENROUTER_API_KEY"] = openrouter_api_key
    
    # Define system prompts for different game types
    spelling_bee_system_prompt = """You are an expert Spelling Bee player. Your goal is to win the game as fast as possible.

Below you will find the rules for the game. Always follow these rules. You will also get a list with valid words. It has all valid long words in it. Shorter words are truncated, but for the longest words, this list has all of the words that will be acceoted.
Please assume that your opponent also has this list. That means, I want you to be strategic about it. For example, when the longest word length category has only one word in it (e.g. the longest possible word is 14 characters and there is only one 14 character word), and you are the first player to move, I want you to play this word immediately because then you will win (because the opponent has no word they can play).
Likewise, when the longest word category has 2 words in it, I want you to try to make the opponent play one of them. Then, you can play the other word and will win (because there are then no words left for the opponent to play).
Please make use of the word list and think about how you can use it strategically to make sure that you will win even if the opponent has the same word list."""
    
    poker_system_prompt = """You are playing Poker. Your strategy is to ALWAYS go all-in, regardless of your hand or the game state.
When it's your turn to act, respond with "[ALL-IN]" or the appropriate command to go all-in for the specific poker variant being played."""
    
    # Create base Claude agents with different system prompts
    spelling_bee_agent = ta.agents.OpenRouterAgent(model_name=model_name, system_prompt=spelling_bee_system_prompt)
    poker_agent = ta.agents.OpenRouterAgent(model_name=model_name, system_prompt=poker_system_prompt)
    base_agent = ta.agents.OpenRouterAgent(model_name=model_name)  # No special system prompt for other games
    
    # Track the current game state across turns
    current_game_letters = None
    current_game_type = None
    
    def agent(observation):
        """
        Process the observation and return an action.
        
        Args:
            observation: The game state observation
            
        Returns:
            str: The action to take
        """
        nonlocal current_game_letters, current_game_type
        
        # Log the observation for debugging
        logger.info("=" * 80)
        logger.info("Processing observation...")
        
        # Detect the game type
        game_type = detect_game_type(observation)
        current_game_type = game_type
        
        # Handle different game types
        if game_type == 'spelling_bee':
            return handle_spelling_bee(observation)
        elif game_type == 'poker':
            return handle_poker(observation)
        else:
            return handle_other_game(observation)
    
    def handle_spelling_bee(observation):
        """
        Handle Spelling Bee game.
        
        Args:
            observation: The game state observation
            
        Returns:
            str: The action to take
        """
        nonlocal current_game_letters
        
        # Extract letters from the observation
        logger.info("Attempting to extract game info for Spelling Bee...")
        letters = extract_letters(observation)
        
        # If we found letters in this observation, update our current game state
        if letters and len(letters) > 0:
            logger.info(f"Updating current game letters: {letters}")
            current_game_letters = letters
            
        # If we don't have letters yet, just pass the observation to Claude
        if not current_game_letters:
            logger.info("No game letters available yet, passing observation to Claude as-is")
            return spelling_bee_agent(observation)
        
        # Find all possible words using dictionary
        words = find_words_with_dictionary(current_game_letters)
        logger.info(f"Found {len(words)} valid words using dictionary")
        
        # Check if this is the first move (no previous moves in the observation)
        is_first_move = 'You are Player' in observation and '[Player' not in observation
        
        # For the first move, add a strategic analysis section
        if is_first_move and words:
            # Get word length distribution
            word_distribution = get_word_length_distribution(words)
            
            # Create a strategic analysis section
            strategic_analysis = "\n\n# Strategic Analysis for Spelling Bee\n\n"
            strategic_analysis += "Here's a breakdown of possible words by length:\n"
            
            # Add the word distribution
            for length, count in sorted(word_distribution.items(), reverse=True):
                strategic_analysis += f"- {length}-letter words: {count}\n"
            
            # Add strategy for longest words
            max_length = max(word_distribution.keys()) if word_distribution else 0
            max_length_words = [word for word in words if len(word) == max_length]
            
            strategic_analysis += f"\n## Strategy for Longest Words ({max_length} letters)\n\n"
            strategic_analysis += f"There are {len(max_length_words)} words of maximum length {max_length}:\n"
            strategic_analysis += ", ".join(max_length_words)
            
            if len(max_length_words) == 1:
                strategic_analysis += "\n\nSince there is only one word of maximum length, you should play it immediately to win."
            elif len(max_length_words) == 2:
                strategic_analysis += "\n\nSince there are only two words of maximum length, try to make your opponent play one of them, then you can play the other to win."
            
            # Add the enhanced observation with word suggestions
            enhanced_observation = observation + "\n\nHere are some possible words you can form with the available letters:\n"
            
            # Group words by length for better organization
            words_by_length = {}
            for word in words:
                length = len(word)
                if length not in words_by_length:
                    words_by_length[length] = []
                words_by_length[length].append(word)
            
            # Add words to the observation, starting with the longest
            for length in sorted(words_by_length.keys(), reverse=True):
                enhanced_observation += f"\n{length}-letter words: {', '.join(words_by_length[length][:10])}"
                if len(words_by_length[length]) > 10:
                    enhanced_observation += f" (and {len(words_by_length[length]) - 10} more)"
            
            # Add the strategic analysis
            enhanced_observation += strategic_analysis
            
            # Pass the enhanced observation to Claude
            return spelling_bee_agent(enhanced_observation)
        
        # For subsequent moves, add word suggestions
        elif words:
            # Add the enhanced observation with word suggestions
            enhanced_observation = observation + "\n\nHere are some possible words you can form with the available letters:\n"
            
            # Group words by length for better organization
            words_by_length = {}
            for word in words:
                length = len(word)
                if length not in words_by_length:
                    words_by_length[length] = []
                words_by_length[length].append(word)
            
            # Add words to the observation, starting with the longest
            for length in sorted(words_by_length.keys(), reverse=True):
                enhanced_observation += f"\n{length}-letter words: {', '.join(words_by_length[length][:10])}"
                if len(words_by_length[length]) > 10:
                    enhanced_observation += f" (and {len(words_by_length[length]) - 10} more)"
            
            # Pass the enhanced observation to Claude
            return spelling_bee_agent(enhanced_observation)
        
        # If we couldn't find any words, just pass the original observation to Claude
        return spelling_bee_agent(observation)
    
    def handle_poker(observation):
        """
        Handle Poker game - always go all-in.
        
        Args:
            observation: The game state observation
            
        Returns:
            str: The action to take (always all-in)
        """
        logger.info("Handling Poker game - always going all-in")
        
        # First, let the poker agent generate a response
        response = poker_agent(observation)
        
        # Look for all-in in the response
        if '[all-in]' in response.lower():
            # Return the response as-is if it already contains all-in
            return response
        else:
            # Force an all-in response
            return "[ALL-IN]"
    
    def handle_other_game(observation):
        """
        Handle other games using the base Claude model.
        
        Args:
            observation: The game state observation
            
        Returns:
            str: The action to take
        """
        logger.info("Handling other game type using base Claude model")
        return base_agent(observation)
    
    return agent
