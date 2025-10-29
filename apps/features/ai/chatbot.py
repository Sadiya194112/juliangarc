"""
Main chatbot logic for EV Charging Assistant.
Coordinates intent detection, service calls, and response generation.
"""
from typing import Optional, Tuple
from apps.features.ai.services import GoogleMapsService, OpenAIService


class EVChargingChatbot:
    """Main chatbot class orchestrating all interactions."""
    
    def __init__(self):
        """Initialize chatbot with required services."""
        self.openai_service = OpenAIService()
        self.maps_service = GoogleMapsService()
    
    def get_response(
        self,
        user_message: str,
        chat_history: list,
        lat: Optional[float] = None,
        lng: Optional[float] = None
    ) -> str:
        """
        Generate a response to the user's message.
        
        Args:
            user_message: The user's input message
            chat_history: List of previous conversation messages
            lat: User's latitude (optional)
            lng: User's longitude (optional)
            
        Returns:
            Bot's response message
        """
        # Detect user intent
        intent = self.openai_service.detect_intent(user_message, chat_history)
        
        # Prepare context and system instruction based on intent
        context, system_instruction = self._prepare_response_context(
            intent, lat, lng
        )
        
        # Handle missing location for find_station intent
        if intent == "find_station" and (lat is None or lng is None):
            return (
                "I can definitely help with that! To find the nearest stations, "
                "I need your location. Could you please share it?"
            )
        
        # Generate final response
        return self.openai_service.generate_response(
            user_message,
            chat_history,
            context,
            system_instruction
        )
    
    def _prepare_response_context(
        self,
        intent: str,
        lat: Optional[float],
        lng: Optional[float]
    ) -> Tuple[str, str]:
        """
        Prepare context and system instruction based on detected intent.
        
        Args:
            intent: Detected user intent
            lat: User's latitude
            lng: User's longitude
            
        Returns:
            Tuple of (context, system_instruction)
        """
        if intent == "find_station":
            if lat and lng:
                context = self.maps_service.find_charging_stations(lat, lng)
            else:
                context = "Location not provided."
            system_instruction = "You are a friendly and helpful EV Charging Assistant chatbot."
        
        elif intent == "general_info":
            context = "No external data needed. Please answer the user's question based on your knowledge."
            system_instruction = (
                "You are an expert on Electric Vehicles. "
                "Answer the user's question about EV charging concisely and accurately."
            )
        
        else:  # intent == "other"
            context = (
                "The user is not asking to find a station or for specific EV info. "
                "Engage in a friendly, brief conversation."
            )
            system_instruction = "You are a friendly and helpful EV Charging Assistant chatbot."
        
        return context, system_instruction
