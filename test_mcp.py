#!/usr/bin/env python
"""
Test script for the MCP agent and server.
"""
import os
import sys
import logging
import asyncio
import json
import aiohttp
import traceback
import nltk

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger('mcp_test')
logger.setLevel(logging.DEBUG)

async def find_words_with_mcp(letters, mcp_server_url):
    """
    Use HTTP requests to find all possible words through the MCP server.
    If the MCP server is unavailable, fall back to using NLTK directly.
    
    Args:
        letters: List of available letters
        mcp_server_url: URL of the MCP server
        
    Returns:
        list: Valid words that can be formed
    """
    try:
        print(f"Finding words with MCP: letters={letters}")
        
        # Create the JSON-RPC request payload
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "call_tool",
            "params": {
                "name": "find_words",
                "input": {
                    "letters": letters
                }
            }
        }
        
        # Make the HTTP request to the MCP server
        async with aiohttp.ClientSession() as session:
            # The MCP server expects JSON-RPC requests at the /jsonrpc endpoint
            print(f"Making request to: {mcp_server_url}/jsonrpc")
            async with session.post(f"{mcp_server_url}/jsonrpc", json=payload) as response:
                if response.status == 200:
                    result_json = await response.json()
                    print(f"MCP response received")
                    
                    if "result" in result_json:
                        words = result_json["result"]
                        print(f"MCP found {len(words)} total words")
                        
                        # Sort words by length (longer words first for higher points)
                        words.sort(key=len, reverse=True)
                        
                        return words
                    elif "error" in result_json:
                        print(f"MCP error: {result_json['error']}")
                        print("Falling back to direct dictionary filtering")
                        return find_words_fallback(letters)
                    else:
                        print("MCP returned an unexpected response format")
                        print("Falling back to direct dictionary filtering")
                        return find_words_fallback(letters)
                else:
                    print(f"HTTP error: {response.status}")
                    response_text = await response.text()
                    print(f"Response: {response_text}")
                    print("Falling back to direct dictionary filtering")
                    return find_words_fallback(letters)
            
    except Exception as e:
        print(f"Error calling MCP: {str(e)}")
        print(traceback.format_exc())
        print("Falling back to direct dictionary filtering")
        return find_words_fallback(letters)

def find_words_fallback(letters):
    """
    Fallback method to find words using NLTK directly.
    
    Args:
        letters: List of available letters
        
    Returns:
        list: Valid words that can be formed
    """
    print("Using fallback method with NLTK")
    
    # Create a set of valid letters (lowercase)
    valid_letters = set(letter.lower() for letter in letters)
    
    # Filter words from nltk corpus
    nltk.download('words', quiet=True)
    from nltk.corpus import words as nltk_words
    
    # Get all English words
    english_words = set(word.lower() for word in nltk_words.words())
    
    # Filter words
    valid_words = []
    for word in english_words:
        # Skip words that are too short
        if len(word) < 4:
            continue
        
        # Check if all letters in the word are in the available letters
        if all(letter in valid_letters for letter in word):
            valid_words.append(word)
    
    print(f"Found {len(valid_words)} valid words using fallback method")
    
    # Sort words by length (longer words first for higher points)
    valid_words.sort(key=len, reverse=True)
    
    return valid_words

async def main_async():
    """Test the MCP agent's word-finding capability asynchronously."""
    # Test letters for the SpellingBee game
    # letters = ["P", "A", "R", "K", "I", "N", "G"]
    #a, c, e, h, i, s, t
    letters = ["A", "C", "E", "H", "I", "S", "T"]
    
    # Try both the HTTP server port and the MCP server port
    mcp_server_url = "http://localhost:8000"
    
    print(f"Testing MCP word-finding with letters: {letters}")
    
    # Find words using the MCP client
    words = await find_words_with_mcp(letters, mcp_server_url)
    
    # Display the results
    if words:
        print(f"Found {len(words)} words:")
        # Show first 10 words
        for word in words[:10]:
            print(f"  - {word}")
        if len(words) > 10:
            print(f"  ... and {len(words) - 10} more")
    else:
        print("No words found")

def main():
    """Run the async main function."""
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
