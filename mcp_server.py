import os
import re
import json
import sys
import threading
import logging
import importlib.resources
from collections import defaultdict
import nltk
from nltk.corpus import words
from mcp.server.fastmcp import FastMCP
import http.server
import socketserver
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to ensure all messages are captured
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Force reconfiguration in case logging was already configured elsewhere
)
logger = logging.getLogger('mcp_server')
logger.setLevel(logging.DEBUG)  # Ensure the logger itself is set to DEBUG level

# Add a console handler to make sure logs are displayed
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Import the dictionary module
from dictionary import dictionary, EnglishDictionary

# Get all English words from the dictionary
english_words = dictionary.get_all_words()
logger.info(f"Loaded {len(english_words)} English words from TextArena dictionary")

# Create an MCP server
mcp = FastMCP("SpellingBee Word Finder")

@mcp.tool()
def find_words(letters: list[str]) -> list[str]:
    """
    Find all valid English words that can be formed using the given letters.
    
    Args:
        letters: List of available letters
        
    Returns:
        list: Valid words that can be formed
    """
    logger.info(f"Finding words with letters: {letters}")
    
    # Convert all letters to lowercase for case-insensitive matching
    letters = [letter.lower() for letter in letters]
    
    # Find all valid words
    valid_words = []
    for word in english_words:
        # Skip words that are too short
        if len(word) < 4:
            continue
        
        # Check if all letters in the word are in the available letters
        valid = True
        for letter in word:
            if letter not in letters:
                valid = False
                break
        
        if valid:
            valid_words.append(word)
    
    logger.info(f"Found {len(valid_words)} valid words")
    return valid_words

# Create a simple HTTP server to expose the find_words function
class FindWordsHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse the URL path and query parameters
            parsed_url = urllib.parse.urlparse(self.path)
            
            # Check if this is a request to the find_words endpoint
            if parsed_url.path == '/find_words':
                # Parse the query parameters
                query_params = urllib.parse.parse_qs(parsed_url.query)
                
                # Get the letters from the query parameters
                letters_param = query_params.get('letters', [''])[0]
                
                # Parse the letters (comma-separated list)
                letters = letters_param.split(',')
                
                # Call the find_words function
                logger.info(f"HTTP request to find_words: letters={letters}")
                words = find_words(letters)
                
                # Return the results as JSON
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(words).encode())
                return
                
            # If not a recognized endpoint, return 404
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
            
        except Exception as e:
            logger.error(f"Error handling HTTP request: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode())

def start_http_server(port=8080):
    """Start a simple HTTP server to expose the find_words function."""
    logger.info(f"Starting HTTP server on port {port}")
    
    # Create the HTTP server
    httpd = socketserver.ThreadingTCPServer(("", port), FindWordsHandler)
    
    # Start the server in a background thread
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    logger.info(f"HTTP server running on port {port}")
    return httpd

def start_server_thread(host='0.0.0.0', port=8000):
    """Start the MCP server in a background thread."""
    logger.info(f"Starting MCP server in background thread")
    
    # Create a command to run the MCP server using the CLI
    cmd = f"mcp run {__file__}"
    
    def run_server():
        logger.info(f"Running command: {cmd}")
        os.system(cmd)
    
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    return server_thread

if __name__ == '__main__':
    # If run directly, start the server
    if 'mcp' in sys.modules:
        # If being run by the MCP CLI, just define the server
        logger.info("Running via MCP CLI")
        
        # Also start the HTTP server for direct access
        start_http_server(port=8080)
    else:
        # If run directly, use the CLI to start the server
        logger.info("Running directly, starting server via CLI")
        os.system(f"mcp run {__file__}")
