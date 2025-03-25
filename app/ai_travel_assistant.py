# ai_travel_assistant.py
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

import openai
from config import config


from travel_assistant_api import TravelAssistantAPI
class AITravelAssistant:
     
    #def __init__(self, config: Dict[str, Any]):
    def __init__(self, config):
        print("Received Config:", config)  # Debugging Step

        if 'api_keys' not in config:
            raise ValueError("Config is missing 'api_keys' key!")

        if 'booking_api_key' not in config['api_keys']:
            raise ValueError("Config['api_keys'] is missing 'booking_api_key'!")

        self.api_service = TravelAssistantAPI(config['api_keys'])  # Pass only the API keys

        """
        Initialize the AI Travel Assistant.
        
        Args:
            config: Dictionary containing API keys and configuration
        """
        #self.api_service = TravelAssistantAPI(config['api_keys'])
        
        openai.api_key = config['openai_api_key']
        self.user_context = {}  # Store user preferences and conversation context


    from travel_assistant_api import TravelAssistantAPI


    async def process_user_query(self, user_id: str, query: str) -> str:
        """
        Process user query and generate response.
        
        Args:
            user_id: Unique identifier for the user
            query: User's natural language query
            
        Returns:
            Natural language response to the user query
        """
        # Get user context or create new one
        user_context = self._get_user_context(user_id)

        # Use LLM to understand the query intent
        intent = await self._identify_query_intent(query, user_context)
        
        # Based on intent, call appropriate API methods
        response = None
        if intent['type'] == 'TRIP_PLANNING':
            response = self.api_service.plan_trip(intent['parameters'])
        elif intent['type'] == 'FLIGHT_STATUS':
            response = self.api_service.get_flight_info(
                intent['parameters']['flight_number'], 
                intent['parameters'].get('date')
            )
        elif intent['type'] == 'TRAVEL_ROUTE':
            response = self.api_service.get_travel_route(
                intent['parameters']['origin'], 
                intent['parameters']['destination']
            )
        # Add more intent handlers as needed
        
        # Generate natural language response using LLM
        conversational_response = await self._generate_response(response, user_context)
        
        # Update user context with new information
        self._update_user_context(user_id, query, response)
        
        return conversational_response

    async def _identify_query_intent(self, query: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use OpenAI to extract intent and parameters from user query.
        
        Args:
            query: User's natural language query
            user_context: User's context information
            
        Returns:
            Dictionary containing intent type and parameters
        """
        prompt = self._build_intent_extraction_prompt(query, user_context)
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )

        return json.loads(response.choices[0].message.content)

    async def _generate_response(self, api_response: Dict[str, Any], user_context: Dict[str, Any]) -> str:
        """
        Use OpenAI to generate natural language response.
        
        Args:
            api_response: Data returned from API calls
            user_context: User's context information
            
        Returns:
            Natural language response
        """
        prompt = self._build_response_generation_prompt(api_response, user_context)
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        return response.choices[0].message.content

    def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get user context or create a new one if it doesn't exist.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            User context dictionary
        """
        if user_id not in self.user_context:
            self.user_context[user_id] = {
                'conversations': [],
                'preferences': {},
                'trip_history': []
            }
        return self.user_context[user_id]

    def _update_user_context(self, user_id: str, query: str, response: Dict[str, Any]) -> None:
        """
        Update user context with new conversation and extracted preferences.
        
        Args:
            user_id: Unique identifier for the user
            query: User's query
            response: API response data
        """
        context = self._get_user_context(user_id)
        
        # Add to conversation history
        context['conversations'].append({
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response': response
        })
        
        # Extract and update preferences if available
        # This would be implemented with another LLM call to extract preferences

    def _build_intent_extraction_prompt(self, query: str, user_context: Dict[str, Any]) -> str:
        """
        Build prompt for intent extraction.
        
        Args:
            query: User's query
            user_context: User's context information
            
        Returns:
            Prompt string for the LLM
        """
        return f"""
        Based on the following user query and context, identify the user's intent and extract relevant parameters.
        
        User query: "{query}"
        
        User context:
        {json.dumps(user_context, indent=2)}
        
        Return a JSON object with the following structure:
        {{
          "type": "INTENT_TYPE", // One of: TRIP_PLANNING, FLIGHT_STATUS, TRAVEL_ROUTE, etc.
          "parameters": {{
            // Relevant parameters for the intent
          }}
        }}
        """

    def _build_response_generation_prompt(self, api_response: Dict[str, Any], user_context: Dict[str, Any]) -> str:
        """
        Build prompt for response generation.
        
        Args:
            api_response: Data returned from API calls
            user_context: User's context information
            
        Returns:
            Prompt string for the LLM
        """
        return f"""
        Generate a natural, conversational response based on the following API data and user context.
        
        API response:
        {json.dumps(api_response, indent=2)}
        
        User context:
        {json.dumps(user_context, indent=2)}
        
        The response should be helpful, personalized, and conversational.
        """