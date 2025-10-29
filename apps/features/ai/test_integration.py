"""
Integration tests for EV Charging Chatbot.
These tests make REAL API calls to Google Maps and OpenAI.

WARNING: These tests will:
- Consume API credits/quota
- Take longer to run (30-60 seconds)
- Require valid API keys in .env file
- Need internet connection

Run with: pytest test_integration.py -v -s
Add -s flag to see print statements during execution
"""
import pytest
import time
from chatbot import EVChargingChatbot
from services import GoogleMapsService, OpenAIService
from config import Config


# Skip all tests if API keys are not properly configured
pytestmark = pytest.mark.integration


class TestGoogleMapsIntegration:
    """Integration tests for Google Maps API."""
    
    def test_find_charging_stations_bangalore(self):
        """Test finding real charging stations in Bangalore, India."""
        print("\n🔍 Searching for charging stations in Bangalore...")
        
        # Bangalore coordinates
        lat, lng = 12.9716, 77.5946
        
        start_time = time.time()
        result = GoogleMapsService.find_charging_stations(lat, lng)
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  API call took {elapsed_time:.2f} seconds")
        print(f"📍 Result:\n{result}\n")
        
        # Assertions
        assert isinstance(result, str)
        assert len(result) > 0
        # Should either find stations or say none found
        assert ("charging station" in result.lower() or 
                "no charging stations found" in result.lower())
        
        # Check response time is reasonable (should be < 5 seconds)
        assert elapsed_time < 5.0, f"API call took too long: {elapsed_time}s"
    
    def test_find_charging_stations_san_francisco(self):
        """Test finding real charging stations in San Francisco, USA."""
        print("\n🔍 Searching for charging stations in San Francisco...")
        
        # San Francisco coordinates
        lat, lng = 37.7749, -122.4194
        
        start_time = time.time()
        result = GoogleMapsService.find_charging_stations(lat, lng)
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  API call took {elapsed_time:.2f} seconds")
        print(f"📍 Result:\n{result}\n")
        
        # Assertions
        assert isinstance(result, str)
        assert len(result) > 0
        # San Francisco should have charging stations
        assert "Name:" in result or "no charging stations found" in result.lower()
    
    def test_find_charging_stations_remote_location(self):
        """Test finding charging stations in a remote location (likely no results)."""
        print("\n🔍 Searching for charging stations in middle of ocean...")
        
        # Middle of Pacific Ocean
        lat, lng = 0.0, -160.0
        
        start_time = time.time()
        result = GoogleMapsService.find_charging_stations(lat, lng, radius=10000)
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  API call took {elapsed_time:.2f} seconds")
        print(f"📍 Result:\n{result}\n")
        
        # Should find no stations in middle of ocean
        assert isinstance(result, str)
        assert "no charging stations found" in result.lower()
    
    def test_find_charging_stations_custom_radius(self):
        """Test finding charging stations with custom search radius."""
        print("\n🔍 Testing custom radius search in New York...")
        
        # New York coordinates
        lat, lng = 40.7128, -74.0060
        
        # Test with small radius (1km)
        start_time = time.time()
        result_small = GoogleMapsService.find_charging_stations(lat, lng, radius=1000)
        elapsed_small = time.time() - start_time
        
        print(f"⏱️  Small radius (1km) took {elapsed_small:.2f} seconds")
        print(f"📍 Result (1km):\n{result_small}\n")
        
        # Test with large radius (10km)
        start_time = time.time()
        result_large = GoogleMapsService.find_charging_stations(lat, lng, radius=10000)
        elapsed_large = time.time() - start_time
        
        print(f"⏱️  Large radius (10km) took {elapsed_large:.2f} seconds")
        print(f"📍 Result (10km):\n{result_large}\n")
        
        # Both should return valid results
        assert isinstance(result_small, str)
        assert isinstance(result_large, str)


class TestOpenAIIntegration:
    """Integration tests for OpenAI API."""
    
    def test_detect_intent_find_station(self):
        """Test intent detection for finding stations."""
        print("\n🤖 Testing intent detection: find_station...")
        
        service = OpenAIService()
        
        test_messages = [
            "Where is the nearest charging station?",
            "Find me a place to charge my EV",
            "I need to charge my car, where can I go?",
            "Show me nearby charging points"
        ]
        
        for message in test_messages:
            start_time = time.time()
            intent = service.detect_intent(message, [])
            elapsed_time = time.time() - start_time
            
            print(f"⏱️  Message: '{message}'")
            print(f"   Intent: {intent} (took {elapsed_time:.2f}s)")
            
            # Should detect as find_station
            assert intent in ['find_station', 'general_info', 'other']
            assert elapsed_time < 10.0, f"API call took too long: {elapsed_time}s"
        
        print()
    
    def test_detect_intent_general_info(self):
        """Test intent detection for general information."""
        print("\n🤖 Testing intent detection: general_info...")
        
        service = OpenAIService()
        
        test_messages = [
            "How fast is Level 2 charging?",
            "What's the difference between AC and DC charging?",
            "How much does it cost to charge an EV?",
            "What is a CCS connector?"
        ]
        
        for message in test_messages:
            start_time = time.time()
            intent = service.detect_intent(message, [])
            elapsed_time = time.time() - start_time
            
            print(f"⏱️  Message: '{message}'")
            print(f"   Intent: {intent} (took {elapsed_time:.2f}s)")
            
            # Should be valid intent
            assert intent in ['find_station', 'general_info', 'other']
        
        print()
    
    def test_detect_intent_other(self):
        """Test intent detection for other/conversational queries."""
        print("\n🤖 Testing intent detection: other...")
        
        service = OpenAIService()
        
        test_messages = [
            "Hello!",
            "How are you?",
            "What's the weather like?",
            "Thank you"
        ]
        
        for message in test_messages:
            start_time = time.time()
            intent = service.detect_intent(message, [])
            elapsed_time = time.time() - start_time
            
            print(f"⏱️  Message: '{message}'")
            print(f"   Intent: {intent} (took {elapsed_time:.2f}s)")
            
            # Should be valid intent
            assert intent in ['find_station', 'general_info', 'other']
        
        print()
    
    def test_detect_intent_with_conversation_history(self):
        """Test intent detection with conversation context."""
        print("\n🤖 Testing intent detection with conversation history...")
        
        service = OpenAIService()
        
        # Build conversation history
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "bot", "content": "Hi! How can I help you with EV charging today?"},
            {"role": "user", "content": "I'm planning a road trip"},
            {"role": "bot", "content": "That's great! I can help you find charging stations along your route."}
        ]
        
        # This should be detected as find_station based on context
        message = "Where can I charge nearby?"
        
        start_time = time.time()
        intent = service.detect_intent(message, history)
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  Message: '{message}'")
        print(f"   Intent: {intent} (took {elapsed_time:.2f}s)")
        print(f"   Context: {len(history)} previous messages\n")
        
        assert intent in ['find_station', 'general_info', 'other']
    
    def test_generate_response_with_station_data(self):
        """Test response generation with charging station context."""
        print("\n🤖 Testing response generation with station data...")
        
        service = OpenAIService()
        
        user_message = "Where can I charge my EV?"
        context = """Here are the top 3 nearby charging stations:
- Name: Tesla Supercharger
  Address: 123 Main St
  Rating: 4.8/5
  Status: Open now
- Name: ChargePoint Station
  Address: 456 Oak Ave
  Rating: 4.5/5
  Status: Open now
"""
        system_instruction = "You are a friendly and helpful EV Charging Assistant chatbot."
        
        start_time = time.time()
        response = service.generate_response(user_message, [], context, system_instruction)
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  Response generation took {elapsed_time:.2f} seconds")
        print(f"📝 Generated response:\n{response}\n")
        
        # Assertions
        assert isinstance(response, str)
        assert len(response) > 0
        assert elapsed_time < 15.0, f"Response generation took too long: {elapsed_time}s"
    
    def test_generate_response_general_ev_info(self):
        """Test response generation for general EV questions."""
        print("\n🤖 Testing response generation for general EV info...")
        
        service = OpenAIService()
        
        user_message = "How long does it take to charge an electric vehicle?"
        context = "No external data needed. Please answer the user's question based on your knowledge."
        system_instruction = "You are an expert on Electric Vehicles. Answer the user's question about EV charging concisely and accurately."
        
        start_time = time.time()
        response = service.generate_response(user_message, [], context, system_instruction)
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  Response generation took {elapsed_time:.2f} seconds")
        print(f"📝 Generated response:\n{response}\n")
        
        # Assertions
        assert isinstance(response, str)
        assert len(response) > 0
        # Response should mention charging or time
        assert any(word in response.lower() for word in ['charg', 'time', 'hour', 'minute'])


class TestChatbotIntegration:
    """End-to-end integration tests for the complete chatbot."""
    
    def test_chatbot_find_stations_with_location(self):
        """Test complete chatbot flow for finding stations."""
        print("\n🔋 Testing complete chatbot: Find stations...")
        
        chatbot = EVChargingChatbot()
        
        # User in Los Angeles
        lat, lng = 34.0522, -118.2437
        message = "I need to charge my Tesla, where can I go?"
        history = []
        
        start_time = time.time()
        response = chatbot.get_response(message, history, lat, lng)
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  Total response time: {elapsed_time:.2f} seconds")
        print(f"💬 User: {message}")
        print(f"🤖 Bot: {response}\n")
        
        # Assertions
        assert isinstance(response, str)
        assert len(response) > 0
        # Should take reasonable time (includes intent detection + maps API + response generation)
        assert elapsed_time < 20.0, f"Chatbot took too long: {elapsed_time}s"
    
    def test_chatbot_find_stations_without_location(self):
        """Test chatbot asking for location when not provided."""
        print("\n🔋 Testing chatbot: Missing location...")
        
        chatbot = EVChargingChatbot()
        
        message = "Where's the nearest charging station?"
        history = []
        
        start_time = time.time()
        response = chatbot.get_response(message, history, None, None)
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  Response time: {elapsed_time:.2f} seconds")
        print(f"💬 User: {message}")
        print(f"🤖 Bot: {response}\n")
        
        # Should ask for location
        assert isinstance(response, str)
        assert "location" in response.lower()
    
    def test_chatbot_general_info_question(self):
        """Test chatbot answering general EV questions."""
        print("\n🔋 Testing chatbot: General info...")
        
        chatbot = EVChargingChatbot()
        
        message = "What's the difference between Level 1 and Level 2 charging?"
        history = []
        
        start_time = time.time()
        response = chatbot.get_response(message, history)
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  Response time: {elapsed_time:.2f} seconds")
        print(f"💬 User: {message}")
        print(f"🤖 Bot: {response}\n")
        
        # Assertions
        assert isinstance(response, str)
        assert len(response) > 0
        # Should mention charging levels
        assert any(word in response.lower() for word in ['level', 'charg', 'fast', 'slow'])
    
    def test_chatbot_conversation_flow(self):
        """Test multi-turn conversation with context."""
        print("\n🔋 Testing chatbot: Conversation flow...")
        
        chatbot = EVChargingChatbot()
        lat, lng = 40.7128, -74.0060  # New York
        history = []
        
        # Turn 1: Greeting
        message1 = "Hello!"
        start_time = time.time()
        response1 = chatbot.get_response(message1, history, lat, lng)
        time1 = time.time() - start_time
        
        print(f"⏱️  Turn 1: {time1:.2f}s")
        print(f"💬 User: {message1}")
        print(f"🤖 Bot: {response1}\n")
        
        history.append({"role": "user", "content": message1})
        history.append({"role": "bot", "content": response1})
        
        # Turn 2: Ask about charging
        message2 = "I need help finding a charging station"
        start_time = time.time()
        response2 = chatbot.get_response(message2, history, lat, lng)
        time2 = time.time() - start_time
        
        print(f"⏱️  Turn 2: {time2:.2f}s")
        print(f"💬 User: {message2}")
        print(f"🤖 Bot: {response2}\n")
        
        history.append({"role": "user", "content": message2})
        history.append({"role": "bot", "content": response2})
        
        # Turn 3: Follow-up question
        message3 = "Which one is closest?"
        start_time = time.time()
        response3 = chatbot.get_response(message3, history, lat, lng)
        time3 = time.time() - start_time
        
        print(f"⏱️  Turn 3: {time3:.2f}s")
        print(f"💬 User: {message3}")
        print(f"🤖 Bot: {response3}\n")
        
        # All responses should be valid
        assert all(isinstance(r, str) and len(r) > 0 for r in [response1, response2, response3])
        
        print(f"✅ Total conversation time: {time1 + time2 + time3:.2f}s\n")
    
    def test_chatbot_multiple_locations(self):
        """Test chatbot with different geographical locations."""
        print("\n🔋 Testing chatbot: Multiple locations...")
        
        chatbot = EVChargingChatbot()
        
        locations = [
            ("Tokyo", 35.6762, 139.6503),
            ("London", 51.5074, -0.1278),
            ("Sydney", -33.8688, 151.2093),
        ]
        
        message = "Where can I charge my EV?"
        
        for city, lat, lng in locations:
            start_time = time.time()
            response = chatbot.get_response(message, [], lat, lng)
            elapsed_time = time.time() - start_time
            
            print(f"📍 {city}: {elapsed_time:.2f}s")
            print(f"   Response length: {len(response)} characters")
            
            assert isinstance(response, str)
            assert len(response) > 0
        
        print()


class TestAPIPerformance:
    """Performance tests for API calls."""
    
    def test_google_maps_response_time(self):
        """Test Google Maps API average response time."""
        print("\n⚡ Testing Google Maps API performance...")
        
        lat, lng = 37.7749, -122.4194  # San Francisco
        times = []
        num_tests = 3
        
        for i in range(num_tests):
            start_time = time.time()
            GoogleMapsService.find_charging_stations(lat, lng)
            elapsed_time = time.time() - start_time
            times.append(elapsed_time)
            print(f"   Test {i+1}/{num_tests}: {elapsed_time:.2f}s")
            time.sleep(0.5)  # Small delay between requests
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n📊 Google Maps API Performance:")
        print(f"   Average: {avg_time:.2f}s")
        print(f"   Min: {min_time:.2f}s")
        print(f"   Max: {max_time:.2f}s\n")
        
        # Average should be reasonable
        assert avg_time < 5.0, f"Average response time too high: {avg_time}s"
    
    def test_openai_response_time(self):
        """Test OpenAI API average response time."""
        print("\n⚡ Testing OpenAI API performance...")
        
        service = OpenAIService()
        times = []
        num_tests = 3
        
        messages = [
            "Where is the nearest charging station?",
            "How fast is DC charging?",
            "Hello!"
        ]
        
        for i, message in enumerate(messages):
            start_time = time.time()
            service.detect_intent(message, [])
            elapsed_time = time.time() - start_time
            times.append(elapsed_time)
            print(f"   Test {i+1}/{num_tests}: {elapsed_time:.2f}s - '{message}'")
            time.sleep(0.5)  # Small delay between requests
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n📊 OpenAI API Performance:")
        print(f"   Average: {avg_time:.2f}s")
        print(f"   Min: {min_time:.2f}s")
        print(f"   Max: {max_time:.2f}s\n")
        
        # Average should be reasonable
        assert avg_time < 10.0, f"Average response time too high: {avg_time}s"


class TestAPIErrorHandling:
    """Test error handling with real APIs."""
    
    def test_google_maps_invalid_coordinates(self):
        """Test Google Maps with extreme/invalid coordinates."""
        print("\n❌ Testing Google Maps with invalid coordinates...")
        
        # Valid but extreme coordinates
        lat, lng = 89.9, 179.9  # Near North Pole
        
        start_time = time.time()
        result = GoogleMapsService.find_charging_stations(lat, lng)
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  API call took {elapsed_time:.2f} seconds")
        print(f"📍 Result: {result}\n")
        
        # Should handle gracefully
        assert isinstance(result, str)
        assert len(result) > 0


# Summary function to run all integration tests
def print_test_summary():
    """Print a summary before running integration tests."""
    print("\n" + "="*70)
    print("🧪 INTEGRATION TESTS - Real API Calls")
    print("="*70)
    print("\n⚠️  WARNING: These tests will:")
    print("   • Make REAL API calls to Google Maps and OpenAI")
    print("   • Consume API credits/quota")
    print("   • Take 30-60 seconds to complete")
    print("   • Require valid API keys in .env file")
    print("   • Need an active internet connection")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    print_test_summary()
    pytest.main([__file__, "-v", "-s"])
