# TextGameStart

A simple implementation of a TextArena SpellingBee agent using Claude 3.7 Sonnet via OpenRouter.

## Overview

This project demonstrates how to use TextArena to create AI agents that play text-based games. The current implementation focuses on the SpellingBee game, where players need to find words that:
- Are at least 4 letters long
- Include a specific center letter
- Only use the provided letters

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Set up your API key:

   a. Rename the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```

   b. Edit the `.env` file and replace `your_openrouter_api_key_here` with your actual OpenRouter API key.

## Usage

Run the agent with:

```bash
python simple_spelling_bee.py
```

## How It Works

The agent uses OpenRouter to access Claude 3.7 Sonnet for playing SpellingBee. The implementation:

1. Sets up two Claude agents to play against each other
2. Initializes the TextArena environment for SpellingBee
3. Runs the game loop where each agent takes turns submitting words
4. Displays the final scores when the game is complete

## Customization

You can modify the agent by:
- Changing the model in the `OpenRouterAgent` initialization
- Adjusting the player names in the `SimpleRenderWrapper`
- Trying different games by changing the `env_id`

## Resources

- [TextArena Documentation](https://textarena.ai/)
- [OpenRouter](https://openrouter.ai/)
- [Anthropic Claude](https://www.anthropic.com/claude)
