# backend/ai_services.py

import google.generativeai as genai
from agno.agent import Agent
from agno.models.google import Gemini
from agno.storage.postgres import PostgresStorage
from agno.media import Image
from textwrap import dedent
from backend.config import settings
import json
from typing import Dict, Any, Optional
import logging
import httpx
import asyncio
from datetime import datetime
from functools import lru_cache

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ASYNCHRONOUS TOOL IMPLEMENTATIONS ---

async def get_market_prices(crop: str, location: str) -> Dict[str, Any]:
    """Gets current market prices for a specific crop in a given location using Google Custom Search."""
    try:
        logger.info(f"Fetching market prices for {crop} in {location}")
        api_key = settings.gemini_api_key
        search_engine_id = settings.market_prices_search_engine_id
        query = f'"{crop}" mandi price in "{location}"'
        url = "https://www.googleapis.com/customsearch/v1"
        params = {'key': api_key, 'cx': search_engine_id, 'q': query, 'num': 3}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=15)
            response.raise_for_status()
            
        search_results = response.json()
        if "items" in search_results and search_results["items"]:
            output = f"📊 **Market Prices for {crop} in {location}**\n\n"
            for item in search_results["items"]:
                title = item.get('title', 'No Title')
                link = item.get('link', '')
                snippet = item.get('snippet', 'No details available.').replace('\n', ' ').strip()
                output += f"**Source:** {title}\n**Details:** {snippet}\n**Link:** {link}\n---\n"
            return {'status': 'success', 'content': output}
        else:
            return {'status': 'error', 'message': f"No live market prices found for '{crop}' in '{location}'."}
    except Exception as e:
        return {'status': 'error', 'message': f"Failed to fetch market prices: {str(e)}"}

async def get_government_schemes(topic: str) -> Dict[str, Any]:
    """Finds relevant Indian government schemes for farmers based on a topic."""
    try:
        logger.info(f"Fetching government schemes for topic: {topic}")
        api_key = settings.gemini_api_key
        search_engine_id = settings.gov_schemes_search_engine_id
        query = f'government schemes and subsidies for "{topic}" for farmers in India'
        url = "https://www.googleapis.com/customsearch/v1"
        params = {'key': api_key, 'cx': search_engine_id, 'q': query, 'num': 3}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=15)
            response.raise_for_status()

        search_results = response.json()
        if "items" in search_results and search_results["items"]:
            output = f"🏛️ **Government Schemes for {topic}**\n\n"
            for item in search_results["items"]:
                title = item.get('title', 'No Title')
                link = item.get('link', '')
                snippet = item.get('snippet', 'No details available.').replace('\n', ' ').strip()
                output += f"**Scheme:** {title}\n**Details:** {snippet}\n**Apply:** {link}\n---\n"
            return {'status': 'success', 'content': output}
        else:
            return {'status': 'error', 'message': f"No government schemes found for '{topic}'."}
    except Exception as e:
        return {'status': 'error', 'message': f"Failed to fetch schemes: {str(e)}"}

async def get_weather_advisory(location: str) -> Dict[str, Any]:
    """Gets a weather forecast for a specific location using a dedicated Google Custom Search."""
    try:
        logger.info(f"Fetching weather advisory for location: {location} using Google Search.")
        api_key = settings.gemini_api_key
        search_engine_id = settings.weather_search_engine_id
        if not search_engine_id:
            return {'status': 'error', 'message': "Weather service is not configured."}
        query = f'weather forecast {location}'
        url = "https://www.googleapis.com/customsearch/v1"
        params = {'key': api_key, 'cx': search_engine_id, 'q': query, 'num': 2}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=15)
            response.raise_for_status()

        search_results = response.json()
        if "items" in search_results and search_results["items"]:
            output = f"🌤️ **Weather Forecast for {location} (from web search)**\n\n"
            for item in search_results["items"]:
                title = item.get('title', 'No Title')
                snippet = item.get('snippet', 'No details available.').replace('\n', ' ').strip()
                link = item.get('link', '')
                output += f"**Source:** {title}\n**Forecast Snippet:** {snippet}\n**More Info:** {link}\n---\n"
            output += "\n**Recommendation:** Please check the links for detailed forecasts."
            return {'status': 'success', 'content': output}
        else:
            return {'status': 'error', 'message': f"Could not find any reliable weather forecasts for '{location}'."}
    except Exception as e:
        return {'status': 'error', 'message': f"Failed to fetch weather data: {str(e)}"}


# --- AGENT DEFINITION & CACHING ---

@lru_cache(maxsize=2)
def get_kisan_agent_definition() -> Agent:
    logger.info("--- Creating and Caching Kisan Mitra Agent Definition ---")
    
    gemini_model = Gemini(
        id="gemini-2.5-flash",
        api_key=settings.gemini_api_key,
        temperature=0.7,
    )
    
    storage = PostgresStorage(
        table_name="agent_sessions",
        db_url=settings.postgres_url,
    )
    
    
    agent_instructions = dedent("""
        <ROLE>
        You are Kisan Mitra, a world-class, multilingual AI agricultural expert. You are fluent in all major Indian languages.
        </ROLE>

        <CONTEXT>
        - User Name: {user_name}
        - User Location: {user_location}
        - Conversation Language: {user_language}
        </CONTEXT>

        ### CRITICAL INSTRUCTION: THE MULTILINGUAL MANDATE ###
        You MUST conduct this entire conversation in the specified "Conversation Language": **{user_language}**.
        - Your analysis, reasoning, and final response must be in **{user_language}**.
        - Do NOT switch to English unless the user explicitly asks you to in English.

        <REASONING_FLOW>
        1.  **Analyze Query**: Fully understand the user's query in **{user_language}**.
        2.  **Assess Context**: Consider the user's location and the current date to provide timely, relevant advice.
        3.  **Select Tools**: If the query is about market prices, weather, or government schemes, decide if a tool is necessary.
        4.  **Synthesize Answer**:
            a. Gather information from your internal knowledge and any selected tools.
            ### CRITICAL TRANSLATION STEP ###
            b. **If tool output is in English, you MUST translate the key information into {user_language} *before* creating your response.** Do not let English text leak into your final answer.
            c. Construct a complete, helpful answer in **{user_language}**.
        </REASONING_FLOW>

        <RESPONSE_PROTOCOL>
        - **Language**: Respond ONLY in **{user_language}**.
        - **Clarity**: Provide a clear, actionable, and step-by-step answer.
        - **Tone**: Be respectful, encouraging, and helpful, like a trusted local expert.
        - **Tool Integration**: Seamlessly weave the translated tool information into your native language response. For example: "ഇന്നത്തെ കാലാവസ്ഥാ റിപ്പോർട്ട് അനുസരിച്ച്..." (According to today's weather report...).
        </RESPONSE_PROTOCOL>
    """)

    return Agent(
        model=gemini_model,
        name="Kisan Mitra - Agricultural Expert",
        storage=storage,
        tools=[get_market_prices, get_government_schemes, get_weather_advisory],
        instructions=agent_instructions,
        markdown=True,
        add_datetime_to_instructions=True,
        debug_mode=False
    )

# --- ASYNC RESPONSE FUNCTIONS ---

async def get_gemini_response(prompt: str, user_info: Dict[str, Any]) -> str:
    """Gets a comprehensive agricultural response using the cached agent."""
    try:
        user_id = str(user_info.get('id', 'anonymous'))
        session_id = f"kisan_session_{user_id}"
        logger.info(f"Processing query: '{prompt}' for session: {session_id}")

        agent = get_kisan_agent_definition()
        agent.session_id = session_id
        agent.user_id = user_id

        formatted_instructions = agent.instructions.format(
            user_name=user_info.get('name', 'Farmer'),
            user_location=user_info.get('location', 'India'),
            user_language=user_info.get('language', 'English') 
        )
        original_instructions = agent.instructions
        agent.instructions = formatted_instructions
        
        response = await agent.arun(prompt)
        
        agent.instructions = original_instructions
        
        return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        logger.error(f"Error getting agricultural response: {e}", exc_info=True)
        return "I'm experiencing technical difficulties while processing your request. Please try again."

async def analyze_visuals(prompt: str, media_content: bytes, mime_type: str, user_info: Dict[str, Any]) -> str:
    try:
        logger.info(f"Processing image analysis for user {user_info.get('id')}")
        
       
        visual_instructions = dedent(f"""
            <ROLE>
            You are an expert plant pathologist and agronomist.
            </ROLE>
            
            <CONTEXT>
            - User Location: {user_info.get('location', 'India')}
            - Conversation Language: {user_info.get('language', 'English')}
            </CONTEXT>

            ### CRITICAL INSTRUCTION ###
            You MUST provide your entire analysis and response in **{user_info.get('language', 'English')}**.
            
            <RESPONSE_PROTOCOL>
            1.  **Observation**: In **{user_info.get('language', 'English')}**, describe what you see in the image.
            2.  **Diagnosis**: In **{user_info.get('language', 'English')}**, state your most likely diagnosis.
            3.  **Immediate Actions**: In **{user_info.get('language', 'English')}**, provide a numbered list of the most urgent steps.
            4.  **Treatment Plan**: In **{user_info.get('language', 'English')}**, suggest treatment options.
            5.  **Prevention**: In **{user_info.get('language', 'English')}**, explain how to prevent this issue.
            </RESPONSE_PROTOCOL>
        """)

        visual_agent = Agent(
            model=get_kisan_agent_definition().model,
            name="Agricultural Diagnostic Specialist",
            instructions=visual_instructions,
            debug_mode=False
        )
        
        image = Image(content=media_content, mime_type=mime_type)
        response = await visual_agent.arun(prompt, images=[image])
        
        return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        logger.error(f"Error in visual analysis: {e}", exc_info=True)
        return "I'm having trouble analyzing the image. Please ensure it's clear and try again."