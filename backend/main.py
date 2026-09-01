"""
MausamVani: Open-Source Multimodal Weather, NWP & Agro-Advisory AI Agent.
Main SDK entrypoint.
"""
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from config import AgentConfig
from core.agent import MultimodalWeatherAgent
from schemas.weather_schemas import MultimodalInput, AgentResponse


def create_agent(ollama_host: str = "http://localhost:11434", llm_model: str = "llama3.1:latest", vision_model: str = "llava:latest") -> MultimodalWeatherAgent:
    """Factory helper to instantiate a configured Multimodal Weather Agent."""
    config = AgentConfig(
        ollama_host=ollama_host,
        llm_model=llm_model,
        vision_model=vision_model
    )
    return MultimodalWeatherAgent(config)


if __name__ == "__main__":
    print("================================================================================")
    print(" MausamVani: Open-Source Multimodal Weather & NWP AI Agent Engine")
    print("================================================================================")
    
    agent = create_agent()
    
    # Run quick sample prompt
    query = "What is the weather and cotton advisory for Nagpur today?"
    print(f"\nProcessing query: '{query}'...")
    response = agent.process_query(MultimodalInput(text_query=query))
    
    print("\n--- Agent Response ---")
    print(response.response_text)
    
    print("\nTo run the full demonstration suite testing all 8 requirements, run:")
    print("python -m examples.demo_all_cases")
