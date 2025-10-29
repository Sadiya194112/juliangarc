import os
import requests
from openai import OpenAI

# --- Initialization ---
# It's best practice to load API keys from environment variables
# For OpenAI API key: https://platform.openai.com/account/api-keys
# For Google Maps API key: https://console.cloud.google.com/google/maps-apis
try:
    GOOGLE_MAPS_API_KEY = os.environ["GOOGLE_MAPS_API_KEY"]
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
    client = OpenAI(api_key=OPENAI_API_KEY)
except KeyError:
    print("🚨 Critical Error: Make sure to set GOOGLE_MAPS_API_KEY and OPENAI_API_KEY environment variables.")
    exit()

def find_nearest_charging_stations(lat: float, lng: float, radius: int = 5000):
    """
    Calls Google Maps Places API to find nearby EV charging stations.
    Uses the recommended 'keyword' parameter instead of the deprecated 'type'.
    """
    url = (
        f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
        f"location={lat},{lng}&radius={radius}&keyword=electric%20vehicle%20charging%20station&key={GOOGLE_MAPS_API_KEY}"
    )

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling Google Maps API: {e}")
        return "Sorry, I'm having trouble accessing mapping services right now."


    if not data.get("results"):
        return "No charging stations found within the search radius."

    # Format the station data nicely for the LLM
    stations = []
    for place in data["results"][:5]: # Limit to top 5 results
        name = place.get("name")
        address = place.get("vicinity")
        rating = place.get("rating", "N/A")
        is_open = "Open now" if place.get("opening_hours", {}).get("open_now") else "May be closed"
        stations.append(f"- Name: {name}\n  Address: {address}\n  Rating: {rating}/5\n  Status: {is_open}")

    return "Here are the top 5 nearby charging stations:\n" + "\n".join(stations)


def get_intent(user_message: str, chat_history):
    """
    Uses OpenAI GPT to classify user intent, now with chat history for context.
    Returns one of: find_station, general_info, other
    """
    prompt = f"""
    You are an intent detection assistant for an EV charging chatbot.
    Based on the latest user message and the conversation history, decide the user's intent.

    CONVERSATION HISTORY:
    {chat_history}

    LATEST USER MESSAGE: "{user_message}"

    Possible intents:
    1. find_station — User asks for nearest/closest/available charging station, directions, or locations.
    2. general_info — User asks general questions about how to charge, plug types, speed, costs, etc.
    3. other — Unrelated, conversational, or unclear queries.

    Respond with ONLY the intent label (find_station / general_info / other).
    """
    try:
        result = client.chat.completions.create(
           model="gpt-4o-mini",
           messages=[{"role": "user", "content": prompt}],
           temperature=0,
        )
        return result.choices[0].message.content.strip().lower()
    except Exception as e:
        print(f"Error getting intent from OpenAI: {e}")
        return "other" # Default to 'other' on error


def chatbot_response(user_message: str, chat_history: list, lat: float = None, lng: float = None):
    """
    Generates a response from the EV chatbot, now with stateful history.
    """
    # Format chat history for prompts
    formatted_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
    intent = get_intent(user_message, formatted_history)
    
    context = ""
    system_instruction = "You are a friendly and helpful EV Charging Assistant chatbot."

    if intent == "find_station":
        if lat and lng:
            context = find_nearest_charging_stations(lat, lng)
        else:
            # If we need location but don't have it.
            return "I can definitely help with that! To find the nearest stations, I need your location. Could you please share it?"

    elif intent == "general_info":
        # For general questions, we don't need external data.
        # We'll let the model answer from its own knowledge.
        system_instruction = "You are an expert on Electric Vehicles. Answer the user's question about EV charging concisely and accurately."
        context = "No external data needed. Please answer the user's question based on your knowledge."

    else: # intent == "other"
        # For conversational or unclear queries.
        context = "The user is not asking to find a station or for specific EV info. Engage in a friendly, brief conversation."

    # --- Final Response Generation ---
    # Construct the full prompt for OpenAI, including the history and new context
    final_prompt_for_user_role = f"""
    Here is the conversation history:
    {formatted_history}

    Here is the relevant data or context for your response:
    ---
    {context}
    ---
    
    Based on all of the above, provide a helpful and natural response to the LATEST user message: "{user_message}"
    """
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": final_prompt_for_user_role},
            ],
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error generating final response from OpenAI: {e}")
        return "I'm sorry, I seem to be having a technical issue. Please try again in a moment."


# -----------------------------
# Example usage with conversation loop
# -----------------------------
if __name__ == "__main__":
    # In a real application, you'd get this from the user's browser/device
    user_latitude, user_longitude = 12.9716, 77.5946
    
    # This list will store the conversation history
    conversation_history = []

    print("🔋 EV Chatbot is online! Type 'quit' to exit.")
    
    while True:
        query = input("You: ")
        if query.lower() == 'quit':
            print("🔋 Chatbot: Goodbye!")
            break

        # Get the chatbot's response
        reply = chatbot_response(query, conversation_history, user_latitude, user_longitude)
        
        # Print the response and update history
        print(f"🤖 Chatbot: {reply}")
        conversation_history.append({"role": "user", "content": query})
        conversation_history.append({"role": "bot", "content": reply})