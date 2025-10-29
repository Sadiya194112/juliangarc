"""
Service modules for EV Charging Chatbot.
Contains Google Maps API and OpenAI API integrations.
"""
import requests
from typing import Optional, Dict, Any
from apps.features.ai.config import config


class GoogleMapsService:
    """Service class for Google Maps API interactions."""
    
    BASE_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    @staticmethod
    def find_charging_stations(
        lat: float,
        lng: float,
        radius: Optional[int] = None
    ) -> str:
        """
        Find nearby EV charging stations using Google Maps Places API.
        
        Args:
            lat: Latitude coordinate
            lng: Longitude coordinate
            radius: Search radius in meters (default from config)
            
        Returns:
            Formatted string with charging station information
        """
        if radius is None:
            radius = config.default_radius
        
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "keyword": "electric vehicle charging station",
            "key": config.google_maps_api_key
        }
        
        try:
            response = requests.get(GoogleMapsService.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error calling Google Maps API: {e}")
            return "Sorry, I'm having trouble accessing mapping services right now."
        
        if not data.get("results"):
            return "No charging stations found within the search radius."
        
        return GoogleMapsService._format_stations(data["results"])
    
    @staticmethod
    def _format_stations(results: list) -> str:
        """
        Format charging station data for display.
        
        Args:
            results: List of place results from Google Maps API
            
        Returns:
            Formatted string with station information
        """
        stations = []
        max_results = config.max_results
        
        for place in results[:max_results]:
            name = place.get("name", "Unknown")
            address = place.get("vicinity", "Address not available")
            rating = place.get("rating", "N/A")
            is_open = "Open now" if place.get("opening_hours", {}).get("open_now") else "May be closed"
            
            stations.append(
                f"- Name: {name}\n"
                f"  Address: {address}\n"
                f"  Rating: {rating}/5\n"
                f"  Status: {is_open}"
            )
        
        return f"Here are the top {len(stations)} nearby charging stations:\n" + "\n".join(stations)


class OpenAIService:
    """Service class for OpenAI API interactions."""
    
    def __init__(self):
        """Initialize OpenAI service with client."""
        self.client = config.get_openai_client()
        self.model = config.openai_model
    
    def detect_intent(self, user_message: str, chat_history: list) -> str:
        """
        Classify user intent using GPT model.
        
        Args:
            user_message: The latest user message
            chat_history: List of previous conversation messages
            
        Returns:
            Intent label: 'find_station', 'general_info', or 'other'
        """
        formatted_history = self._format_chat_history(chat_history)
        
        prompt = f"""
You are an intent detection assistant for an EV charging chatbot.
Based on the latest user message and the conversation history, decide the user's intent.

CONVERSATION HISTORY:
{formatted_history}

LATEST USER MESSAGE: "{user_message}"

Possible intents:
1. find_station — User asks for nearest/closest/available charging station, directions, or locations.
2. general_info — User asks general questions about how to charge, plug types, speed, costs, etc.
3. other — Unrelated, conversational, or unclear queries.

Respond with ONLY the intent label (find_station / general_info / other).
"""
        
        try:
            result = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            return result.choices[0].message.content.strip().lower()
        except Exception as e:
            print(f"Error getting intent from OpenAI: {e}")
            return "other"
    
    def generate_response(
        self,
        user_message: str,
        chat_history: list,
        context: str,
        system_instruction: str
    ) -> str:
        """
        Generate a chatbot response using GPT model.
        
        Args:
            user_message: The latest user message
            chat_history: List of previous conversation messages
            context: Relevant context for the response
            system_instruction: System-level instruction for the AI
            
        Returns:
            Generated response text
        """
        formatted_history = self._format_chat_history(chat_history)
        
        final_prompt = f"""
Here is the conversation history:
{formatted_history}

Here is the relevant data or context for your response:
---
{context}
---

Based on all of the above, provide a helpful and natural response to the LATEST user message: "{user_message}"
"""
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": final_prompt},
                ],
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Error generating final response from OpenAI: {e}")
            return "I'm sorry, I seem to be having a technical issue. Please try again in a moment."
    
    @staticmethod
    def _format_chat_history(chat_history: list) -> str:
        """
        Format chat history for prompt inclusion.
        
        Args:
            chat_history: List of message dictionaries
            
        Returns:
            Formatted string of chat history
        """
        if not chat_history:
            return "No previous conversation."
        
        return "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in chat_history
        ])
