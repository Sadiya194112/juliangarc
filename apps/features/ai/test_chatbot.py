"""
Comprehensive test suite for EV Charging Chatbot.
Tests all modules using pytest with mocking.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os


# Test Config Module
class TestConfig:
    """Test cases for configuration module."""
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key',
        'DEFAULT_SEARCH_RADIUS': '3000',
        'MAX_RESULTS': '10'
    })
    def test_config_initialization_success(self):
        """Test successful configuration initialization."""
        from config import Config
        
        config = Config()
        assert config.google_maps_api_key == 'test_google_key'
        assert config.openai_api_key == 'test_openai_key'
        assert config.default_radius == 3000
        assert config.max_results == 10
    
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test_openai_key'
    }, clear=True)
    def test_config_missing_google_maps_key(self):
        """Test configuration fails without Google Maps API key."""
        from config import Config
        
        with pytest.raises(ValueError, match="GOOGLE_MAPS_API_KEY"):
            Config()
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key'
    }, clear=True)
    def test_config_missing_openai_key(self):
        """Test configuration fails without OpenAI API key."""
        from config import Config
        
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            Config()
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key'
    })
    def test_config_default_values(self):
        """Test configuration uses default values when not specified."""
        from config import Config
        
        config = Config()
        assert config.default_radius == 5000  # Default
        assert config.max_results == 5  # Default
        assert config.openai_model == "gpt-4o-mini"  # Default


# Test Google Maps Service
class TestGoogleMapsService:
    """Test cases for Google Maps service."""
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('services.requests.get')
    def test_find_charging_stations_success(self, mock_get):
        """Test successful charging station search."""
        from services import GoogleMapsService
        
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'results': [
                {
                    'name': 'Station A',
                    'vicinity': '123 Main St',
                    'rating': 4.5,
                    'opening_hours': {'open_now': True}
                },
                {
                    'name': 'Station B',
                    'vicinity': '456 Oak Ave',
                    'rating': 4.0,
                    'opening_hours': {'open_now': False}
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = GoogleMapsService.find_charging_stations(12.9716, 77.5946)
        
        assert 'Station A' in result
        assert 'Station B' in result
        assert '123 Main St' in result
        assert '456 Oak Ave' in result
        assert '4.5/5' in result
        assert 'Open now' in result
        assert 'May be closed' in result
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('services.requests.get')
    def test_find_charging_stations_no_results(self, mock_get):
        """Test handling of no results."""
        from services import GoogleMapsService
        
        mock_response = Mock()
        mock_response.json.return_value = {'results': []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = GoogleMapsService.find_charging_stations(12.9716, 77.5946)
        
        assert 'No charging stations found' in result
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('services.requests.get')
    def test_find_charging_stations_api_error(self, mock_get):
        """Test handling of API errors."""
        from services import GoogleMapsService
        import requests
        
        mock_get.side_effect = requests.exceptions.RequestException("API Error")
        
        result = GoogleMapsService.find_charging_stations(12.9716, 77.5946)
        
        assert 'trouble accessing mapping services' in result
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('services.requests.get')
    def test_find_charging_stations_custom_radius(self, mock_get):
        """Test charging station search with custom radius."""
        from services import GoogleMapsService
        
        mock_response = Mock()
        mock_response.json.return_value = {'results': []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        GoogleMapsService.find_charging_stations(12.9716, 77.5946, radius=10000)
        
        # Verify the radius parameter was passed
        call_args = mock_get.call_args
        assert call_args[1]['params']['radius'] == 10000


# Test OpenAI Service
class TestOpenAIService:
    """Test cases for OpenAI service."""
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('config.OpenAI')
    def test_detect_intent_find_station(self, mock_openai_class):
        """Test intent detection for finding stations."""
        from services import OpenAIService
        
        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='find_station'))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        service = OpenAIService()
        intent = service.detect_intent("Where is the nearest charging station?", [])
        
        assert intent == 'find_station'
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('config.OpenAI')
    def test_detect_intent_general_info(self, mock_openai_class):
        """Test intent detection for general information."""
        from services import OpenAIService
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='general_info'))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        service = OpenAIService()
        intent = service.detect_intent("How fast is Level 2 charging?", [])
        
        assert intent == 'general_info'
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('config.OpenAI')
    def test_detect_intent_error_handling(self, mock_openai_class):
        """Test intent detection error handling."""
        from services import OpenAIService
        
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        service = OpenAIService()
        intent = service.detect_intent("Hello", [])
        
        # Should default to 'other' on error
        assert intent == 'other'
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('config.OpenAI')
    def test_generate_response_success(self, mock_openai_class):
        """Test successful response generation."""
        from services import OpenAIService
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='Here are some charging stations...'))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        service = OpenAIService()
        response = service.generate_response(
            "Where can I charge?",
            [],
            "Station data here",
            "You are a helpful assistant"
        )
        
        assert 'charging stations' in response
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('config.OpenAI')
    def test_generate_response_error_handling(self, mock_openai_class):
        """Test response generation error handling."""
        from services import OpenAIService
        
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        service = OpenAIService()
        response = service.generate_response(
            "Where can I charge?",
            [],
            "Station data",
            "System instruction"
        )
        
        assert 'technical issue' in response


# Test Chatbot
class TestEVChargingChatbot:
    """Test cases for the main chatbot class."""
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('chatbot.OpenAIService')
    @patch('chatbot.GoogleMapsService')
    def test_get_response_find_station_with_location(self, mock_maps, mock_openai):
        """Test chatbot response for finding stations with location."""
        from chatbot import EVChargingChatbot
        
        # Mock services
        mock_openai_instance = Mock()
        mock_openai_instance.detect_intent.return_value = 'find_station'
        mock_openai_instance.generate_response.return_value = 'Here are nearby stations...'
        mock_openai.return_value = mock_openai_instance
        
        mock_maps_instance = Mock()
        mock_maps_instance.find_charging_stations.return_value = 'Station A, Station B'
        mock_maps.return_value = mock_maps_instance
        
        chatbot = EVChargingChatbot()
        response = chatbot.get_response("Find charging stations", [], 12.9716, 77.5946)
        
        assert 'nearby stations' in response
        mock_maps_instance.find_charging_stations.assert_called_once_with(12.9716, 77.5946)
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('chatbot.OpenAIService')
    @patch('chatbot.GoogleMapsService')
    def test_get_response_find_station_without_location(self, mock_maps, mock_openai):
        """Test chatbot response for finding stations without location."""
        from chatbot import EVChargingChatbot
        
        mock_openai_instance = Mock()
        mock_openai_instance.detect_intent.return_value = 'find_station'
        mock_openai.return_value = mock_openai_instance
        
        chatbot = EVChargingChatbot()
        response = chatbot.get_response("Find charging stations", [], None, None)
        
        assert 'need your location' in response
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('chatbot.OpenAIService')
    @patch('chatbot.GoogleMapsService')
    def test_get_response_general_info(self, mock_maps, mock_openai):
        """Test chatbot response for general information."""
        from chatbot import EVChargingChatbot
        
        mock_openai_instance = Mock()
        mock_openai_instance.detect_intent.return_value = 'general_info'
        mock_openai_instance.generate_response.return_value = 'Level 2 charging takes 4-6 hours...'
        mock_openai.return_value = mock_openai_instance
        
        chatbot = EVChargingChatbot()
        response = chatbot.get_response("How fast is Level 2 charging?", [])
        
        assert 'Level 2 charging' in response
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('chatbot.OpenAIService')
    @patch('chatbot.GoogleMapsService')
    def test_get_response_other_intent(self, mock_maps, mock_openai):
        """Test chatbot response for other intents."""
        from chatbot import EVChargingChatbot
        
        mock_openai_instance = Mock()
        mock_openai_instance.detect_intent.return_value = 'other'
        mock_openai_instance.generate_response.return_value = 'Hello! How can I help you today?'
        mock_openai.return_value = mock_openai_instance
        
        chatbot = EVChargingChatbot()
        response = chatbot.get_response("Hello", [])
        
        assert 'Hello' in response
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('chatbot.OpenAIService')
    @patch('chatbot.GoogleMapsService')
    def test_prepare_response_context_find_station(self, mock_maps, mock_openai):
        """Test context preparation for find_station intent."""
        from chatbot import EVChargingChatbot
        
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        
        mock_maps_instance = Mock()
        mock_maps_instance.find_charging_stations.return_value = 'Station data'
        mock_maps.return_value = mock_maps_instance
        
        chatbot = EVChargingChatbot()
        context, system_instruction = chatbot._prepare_response_context(
            'find_station', 12.9716, 77.5946
        )
        
        assert context == 'Station data'
        assert 'EV Charging Assistant' in system_instruction
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('chatbot.OpenAIService')
    @patch('chatbot.GoogleMapsService')
    def test_prepare_response_context_general_info(self, mock_maps, mock_openai):
        """Test context preparation for general_info intent."""
        from chatbot import EVChargingChatbot
        
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        
        chatbot = EVChargingChatbot()
        context, system_instruction = chatbot._prepare_response_context(
            'general_info', None, None
        )
        
        assert 'No external data needed' in context
        assert 'expert on Electric Vehicles' in system_instruction


# Fixtures
@pytest.fixture
def mock_env_vars():
    """Fixture to provide mock environment variables."""
    with patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key'
    }):
        yield


# Test Helper Functions
class TestHelperFunctions:
    """Test cases for helper functions."""
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('config.OpenAI')
    def test_format_chat_history_empty(self, mock_openai_class):
        """Test formatting empty chat history."""
        from services import OpenAIService
        
        result = OpenAIService._format_chat_history([])
        assert result == "No previous conversation."
    
    @patch.dict(os.environ, {
        'GOOGLE_MAPS_API_KEY': 'test_google_key',
        'OPENAI_API_KEY': 'test_openai_key'
    })
    @patch('config.OpenAI')
    def test_format_chat_history_with_messages(self, mock_openai_class):
        """Test formatting chat history with messages."""
        from services import OpenAIService
        
        history = [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'bot', 'content': 'Hi there!'}
        ]
        
        result = OpenAIService._format_chat_history(history)
        assert 'user: Hello' in result
        assert 'bot: Hi there!' in result
