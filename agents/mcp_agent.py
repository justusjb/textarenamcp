import os
import json
import re
import random
import traceback
import textarena as ta
from dotenv import load_dotenv
import logging

# Import the dictionary module
from dictionary import dictionary, EnglishDictionary

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to ensure all messages are captured
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Force reconfiguration in case logging was already configured elsewhere
)
logger = logging.getLogger('mcp_agent')
logger.setLevel(logging.DEBUG)  # Ensure the logger itself is set to DEBUG level

# Add a console handler to make sure logs are displayed
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class DictionaryAgent(ta.agents.OpenRouterAgent):
    """
    An agent that uses a dictionary to enhance Claude's capabilities.
    """
    
    def __init__(self, model_name, description=None):
        """
        Initialize the dictionary agent.
        
        Args:
            model_name: The name of the model to use
            description: A description of the agent
        """
        super().__init__(model_name, description)
        self.current_game_letters = None
        
    async def process_observation(self, observation, state=None):
        """
        Process an observation from the environment.
        
        Args:
            observation: The observation from the environment
            state: The current state of the agent
            
        Returns:
            The processed observation
        """
        # Log the observation for debugging
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("Processing observation:")
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        
        # Log the first 5000 characters to quickly identify the format
        print(f"First 5000 chars: {observation[:5000]}")
        
        # Check if observation is empty or None
        if not observation:
            print("Empty observation received")
            return observation
        
        # Try to extract the allowed letters from the observation
        letters = extract_letters(observation)
        
        # Update the current game letters if we found them
        if letters:
            print(f"Updating current game letters: {letters}")
            self.current_game_letters = letters
        else:
            print("No game letters available yet, passing observation to Claude as-is")
        
        # If we have game letters, enhance the observation with word suggestions
        if self.current_game_letters:
            # Find words with dictionary
            words = find_words_with_dictionary(self.current_game_letters)
            
            if words:
                # Add the word suggestions to the observation
                word_suggestions = "\n\nHere are some possible words you can form with the available letters:\n"
                
                # Group words by length for better organization
                words_by_length = {}
                for word in words:
                    length = len(word)
                    if length not in words_by_length:
                        words_by_length[length] = []
                    words_by_length[length].append(word)
                
                # Add words to the observation, starting with the longest
                for length in sorted(words_by_length.keys(), reverse=True):
                    word_suggestions += f"\n{length}-letter words: {', '.join(words_by_length[length][:10])}"
                    if len(words_by_length[length]) > 10:
                        word_suggestions += f" (and {len(words_by_length[length]) - 10} more)"
                
                # Add the word suggestions to the observation
                enhanced_observation = observation + word_suggestions
                return enhanced_observation
        
        # If we don't have game letters or couldn't find words, just return the original observation
        return observation

def create_dictionary_agent(model_name="anthropic/claude-3.7-sonnet"):
    """
    Create an agent that uses Claude via OpenRouter and enhances it with dictionary for word finding.
    
    Args:
        model_name: The model to use via OpenRouter
        
    Returns:
        A function that processes observations and returns actions
    """
    # Load environment variables
    load_dotenv()
    print("Loading environment variables")
    
    # Get the OpenRouter API key
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        raise ValueError("Please set the OPENROUTER_API_KEY environment variable in your .env file")
    
    # Set the OpenRouter API key
    os.environ["OPENROUTER_API_KEY"] = openrouter_api_key
    
    # Define a system prompt for the agent
    system_prompt = """You are an expert Spelling Bee player. Your goal is to win the game as fast as possible.

Below you will find the rules for the game. Always follow these rules. You will also get a list with valid words. It has all valid long words in it. Shorter words are truncated, but for the longest words, this list has all of the words that will be acceoted.
Please assume that your opponent also has this list. That means, I want you to be strategic about it. For example, when the longest word length category has only one word in it (e.g. the longest possible word is 14 characters and there is only one 14 character word), and you are the first player to move, I want you to play this word immediately because then you will win (because the opponent has no word they can play).
Likewise, when the longest word category has 2 words in it, I want you to try to make the opponent play one of them. Then, you can play the other word and will win (because there are then no words left for the opponent to play).
Please make use of the word list and think about how you can use it strategically to make sure that you will win even if the opponent has the same word list."""
    
    # Create the base Claude agent with the system prompt
    claude_agent = ta.agents.OpenRouterAgent(model_name=model_name, system_prompt=system_prompt)
    
    # Track the current game state across turns
    current_game_letters = None
    
    def agent(observation):
        """
        Process the observation and return an action.
        
        Args:
            observation: The game state observation
            
        Returns:
            str: The action to take
        """
        nonlocal current_game_letters
        
        # Log the full observation to see its format
        print("=" * 80)
        print("INPUT OBSERVATION (START) >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print(observation)
        print("INPUT OBSERVATION (END) <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        print("=" * 80)
        
        # Log observation type and length for debugging
        print(f"Observation type: {type(observation)}")
        print(f"Observation length: {len(observation) if isinstance(observation, str) else 'not a string'}")
        
        # Extract letters from the observation
        print("Attempting to extract game info...")
        letters = extract_letters(observation)
        
        # Log the extraction results
        if letters:
            print(f"Successfully extracted letters: {letters}")
        else:
            print("Failed to extract letters from observation")
            
        # If we found letters in this observation, update our current game state
        if letters and len(letters) > 0:
            print(f"Updating current game letters: {letters}")
            current_game_letters = letters
            
        # If we don't have letters yet, just pass the observation to Claude
        if not current_game_letters:
            print("No game letters available yet, passing observation to Claude as-is")
            return claude_agent(observation)
        
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
            strategic_analysis += "I need to analyze the word distribution carefully to develop a winning strategy:\n\n"
            
            # Add distribution information
            strategic_analysis += "## Word Length Distribution\n"
            for length in sorted(word_distribution.keys(), reverse=True):
                strategic_analysis += f"- {length}-letter words: {word_distribution[length]} words\n"
            
            # Add strategic insights
            strategic_analysis += "\n## Strategic Insights\n"
            
            # Check for special cases that lead to immediate wins
            max_length = max(word_distribution.keys()) if word_distribution else 0
            
            if max_length > 0 and word_distribution[max_length] == 1:
                strategic_analysis += f"- There is only one word of maximum length ({max_length}). Playing it immediately would force a win.\n"
            elif max_length > 0 and word_distribution[max_length] == 2:
                strategic_analysis += f"- There are only two words of maximum length ({max_length}). I should try to make the opponent play one, then I can play the other to win.\n"
            else:
                strategic_analysis += "- I should play shorter words first to force the opponent into playing longer words.\n"
                strategic_analysis += "- This will eventually lead to a situation where the opponent has no valid moves.\n"
            
            # Add the strategic analysis to the observation
            observation = observation + strategic_analysis
        
        # Enhance the observation with the dictionary results
        enhanced_observation = enhance_observation_with_word_results(observation, words)
        
        # Log the enhanced observation
        print("=" * 80)
        print("ENHANCED OBSERVATION (START) >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print(enhanced_observation)
        print("ENHANCED OBSERVATION (END) <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        print("=" * 80)
        
        # Pass the enhanced observation to Claude
        response = claude_agent(enhanced_observation)
        
        # Add a prefix to the response to make it easier to extract the word
        if is_first_move and words:
            # Get the word from the response
            word_match = re.search(r'\[([a-zA-Z]+)\]', response)
            if word_match:
                word = word_match.group(0)
                # Add a prefix to make it clear this is the chosen word
                response = f"After strategic analysis, I choose: {word}\n\n{response}"
        
        return response
    
    return agent

def extract_letters(observation):
    """
    Extract the allowed letters from the observation.
    
    Args:
        observation: The game state observation
        
    Returns:
        A list of allowed letters, or None if not found
    """
    print("Attempting to extract letters")
    
    # Look specifically for the "Allowed Letters: aehktvw" format
    pattern = r"Allowed Letters: ([a-zA-Z]+)"
    match = re.search(pattern, observation, re.IGNORECASE)
    if match:
        letters_str = match.group(1)
        letters = [letter.lower() for letter in letters_str]
        print(f"Extracted letters: {letters}")
        return letters
    else:
        print(f"No match found for 'Allowed Letters:' format")
        print(f"Regex pattern used: {pattern}")
    
    # If we couldn't match the pattern, return None
    return None

def find_words_with_dictionary(letters):
    """
    Use the dictionary to find all possible words.
    
    Args:
        letters: List of available letters
        
    Returns:
        list: Valid words that can be formed
    """
    logger.info(f"Finding words with dictionary: letters={letters}")
    
    # Convert letters to lowercase for matching
    letters = [letter.lower() for letter in letters]
    
    # Filter the dictionary to find valid words
    valid_words = []
    for word in dictionary:
        # Check if the word can be formed using the available letters
        if all(letter.lower() in letters for letter in word):
            valid_words.append(word)
    
    logger.info(f"Found {len(valid_words)} valid words using dictionary")
    return valid_words

def get_word_length_distribution(words):
    """
    Helper function to get distribution of word lengths.
    
    Args:
        words: List of words
        
    Returns:
        dict: Dictionary mapping word length to count
    """
    distribution = {}
    for word in words:
        length = len(word)
        if length not in distribution:
            distribution[length] = 0
        distribution[length] += 1
    return distribution

def enhance_observation_with_word_results(observation, words):
    """
    Enhance the observation with word results.
    
    Args:
        observation: The original observation
        words: List of words found
        
    Returns:
        str: Enhanced observation
    """
    if not words:
        return observation
    
    # Add a section with word suggestions
    enhanced_observation = observation + "\n\n"
    enhanced_observation += "Here are some possible words you can form with the available letters:\n"
    
    # Group words by length for better organization
    words_by_length = {}
    for word in words:
        length = len(word)
        if length not in words_by_length:
            words_by_length[length] = []
        words_by_length[length].append(word)
    
    # Add words to the observation, starting with the longest
    for length in sorted(words_by_length.keys(), reverse=True):
        word_list = words_by_length[length]
        # Limit to 10 words per length to avoid overwhelming Claude
        display_words = word_list[:10]
        enhanced_observation += f"\n{length}-letter words: {', '.join(display_words)}"
        if len(word_list) > 10:
            enhanced_observation += f" (and {len(word_list) - 10} more)"
    
    return enhanced_observation
