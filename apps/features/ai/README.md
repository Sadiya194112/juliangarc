# EV Charging Chatbot 🔋

A conversational AI chatbot that helps users find nearby EV charging stations and provides information about electric vehicle charging. Built with OpenAI GPT and Google Maps API.

## Features

- 🗺️ **Find Nearby Charging Stations**: Get real-time information about nearby EV charging stations
- 💬 **Conversational AI**: Natural language understanding using OpenAI GPT
- 📍 **Location-Based Search**: Searches for stations within a customizable radius
- ℹ️ **General EV Information**: Answers questions about charging speeds, plug types, and more
- 🔄 **Context-Aware**: Maintains conversation history for better responses

## Project Structure

```
Julian/
├── config.py              # Configuration and environment variable management
├── services.py            # Google Maps and OpenAI API service classes
├── chatbot.py            # Main chatbot logic and orchestration
├── main.py               # CLI entry point for interactive chat
├── test_chatbot.py       # Comprehensive pytest test suite
├── ai_logic.py           # Original monolithic code (deprecated)
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (do not commit!)
├── .env.example          # Example environment variables template
├── .gitignore           # Git ignore file
└── README.md            # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/account/api-keys))
- Google Maps API key ([Get one here](https://console.cloud.google.com/google/maps-apis))

### 2. Installation

Clone the repository and navigate to the project directory:

```bash
cd "/home/tanzir/Downloads/Julian"
```

Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configuration

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your actual API keys:

```env
OPENAI_API_KEY=your_actual_openai_api_key_here
GOOGLE_MAPS_API_KEY=your_actual_google_maps_api_key_here
```

**Optional Configuration:**

```env
DEFAULT_SEARCH_RADIUS=5000    # Search radius in meters
MAX_RESULTS=5                 # Maximum number of stations to return
OPENAI_MODEL=gpt-4o-mini     # OpenAI model to use
```

### 4. Running the Chatbot

Start the interactive chatbot:

```bash
python main.py
```

Example conversation:

```
🔋 EV Chatbot is online! Type 'quit' to exit.
📍 Using location: 12.9716, 77.5946

You: Where is the nearest charging station?
🤖 Chatbot: Here are the top 5 nearby charging stations:
- Name: Tesla Supercharger
  Address: 123 Main Street
  Rating: 4.8/5
  Status: Open now
...

You: How fast is Level 2 charging?
🤖 Chatbot: Level 2 charging typically takes 4-6 hours for a full charge...

You: quit
🔋 Chatbot: Goodbye! Drive green! 🌱
```

## Running Tests

### Unit Tests (Fast, Mocked - 0.35s)

Run the complete mock test suite:

```bash
pytest test_chatbot.py -v
```

Run tests with coverage report:

```bash
pytest test_chatbot.py -v --cov=. --cov-report=html
```

Run specific test class:

```bash
pytest test_chatbot.py::TestConfig -v
```

### Integration Tests (Real API Calls - 30-60s)

⚠️ **WARNING**: Integration tests make REAL API calls and consume credits!

Run all integration tests:

```bash
pytest test_integration.py -v -s
```

Run specific integration test class:

```bash
pytest test_integration.py::TestGoogleMapsIntegration -v -s
pytest test_integration.py::TestOpenAIIntegration -v -s
pytest test_integration.py::TestChatbotIntegration -v -s
```

Run performance tests only:

```bash
pytest test_integration.py::TestAPIPerformance -v -s
```

The `-s` flag shows print statements during test execution so you can see real-time progress.

## Module Documentation

### config.py

Manages configuration and environment variables. Validates API keys and provides default values.

**Key Classes:**
- `Config`: Loads and validates environment variables

### services.py

Contains service classes for external API integrations.

**Key Classes:**
- `GoogleMapsService`: Handles Google Maps Places API calls
- `OpenAIService`: Manages OpenAI GPT API interactions

### chatbot.py

Main chatbot orchestration logic.

**Key Classes:**
- `EVChargingChatbot`: Coordinates intent detection, service calls, and response generation

### main.py

Command-line interface for interactive chatbot sessions.

## API Usage

### Using the Chatbot Programmatically

```python
from chatbot import EVChargingChatbot

# Initialize chatbot
chatbot = EVChargingChatbot()

# User's location
latitude = 12.9716
longitude = 77.5946

# Conversation history
history = []

# Get response
user_message = "Where can I charge my EV?"
response = chatbot.get_response(user_message, history, latitude, longitude)

# Update history
history.append({"role": "user", "content": user_message})
history.append({"role": "bot", "content": response})
```

## Development

### Code Style

Format code with Black:

```bash
black *.py
```

Check code quality with flake8:

```bash
flake8 *.py --max-line-length=100
```

### Type Checking

Run mypy for type checking:

```bash
mypy *.py --ignore-missing-imports
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `GOOGLE_MAPS_API_KEY` | Yes | - | Google Maps API key |
| `DEFAULT_SEARCH_RADIUS` | No | 5000 | Search radius in meters |
| `MAX_RESULTS` | No | 5 | Max charging stations to return |
| `OPENAI_MODEL` | No | gpt-4o-mini | OpenAI model name |

## Troubleshooting

### Missing API Keys

If you see: `🚨 Critical Error: GOOGLE_MAPS_API_KEY environment variable is not set`

**Solution:** Make sure you've created a `.env` file with valid API keys.

### Import Errors

If you get import errors:

**Solution:** Make sure you've installed all dependencies:
```bash
pip install -r requirements.txt
```

### API Rate Limits

If you encounter rate limit errors from OpenAI or Google Maps:

**Solution:** Implement retry logic or reduce request frequency. Consider upgrading your API plan.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest test_chatbot.py -v`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is provided as-is for educational and development purposes.

## Acknowledgments

- OpenAI for GPT API
- Google Maps Platform for Places API
- Python community for excellent libraries

## Contact

For questions or support, please open an issue in the repository.

---

**Happy Charging! ⚡🚗**
