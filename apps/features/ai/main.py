"""
Main entry point for EV Charging Chatbot.
Runs an interactive command-line conversation loop.
"""
from chatbot import EVChargingChatbot


def main():
    """Run the chatbot in interactive mode."""
    # Initialize chatbot
    chatbot = EVChargingChatbot()
    
    # In a real application, you'd get this from the user's browser/device
    # Default location: Bangalore, India
    user_latitude, user_longitude = 12.9716, 77.5946
    
    # Store conversation history
    conversation_history = []
    
    print("🔋 EV Chatbot is online! Type 'quit' to exit.")
    print(f"📍 Using location: {user_latitude}, {user_longitude}\n")
    
    while True:
        try:
            query = input("You: ")
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("🔋 Chatbot: Goodbye! Drive green! 🌱")
                break
            
            if not query.strip():
                continue
            
            # Get the chatbot's response
            reply = chatbot.get_response(
                query,
                conversation_history,
                user_latitude,
                user_longitude
            )
            
            # Print the response and update history
            print(f"🤖 Chatbot: {reply}\n")
            conversation_history.append({"role": "user", "content": query})
            conversation_history.append({"role": "bot", "content": reply})
            
        except KeyboardInterrupt:
            print("\n🔋 Chatbot: Goodbye! Drive green! 🌱")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try again.\n")


if __name__ == "__main__":
    main()
