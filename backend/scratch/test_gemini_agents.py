import asyncio
import sys
import os

# Adjust path to import app package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.services.gemini import gemini_agent_service

async def test_gemini_agents():
    print("Starting Gemini Multi-Agent Layer test...")
    
    agents = ["crowd", "volunteer", "medical", "security", "accessibility", "transportation", "sustainability", "executive"]
    
    print(f"Verifying all 8 agents exist in the system...")
    for agent_id in agents:
        assert agent_id in gemini_agent_service.agents_prompts, f"Agent {agent_id} is missing prompt configuration"
        print(f"✓ Agent '{agent_id}' prompt registered successfully.")

    # Test streaming and fallback behavior for the 'crowd' agent
    print("\nTesting streaming response for 'crowd' agent...")
    stream_output = []
    async for chunk in gemini_agent_service.chat_stream(
        agent_id="crowd",
        message="What is the current crowd congestion status?",
        context={"request_source": "test_suite"}
    ):
        sys.stdout.write(chunk)
        sys.stdout.flush()
        stream_output.append(chunk)
    
    print("\n\n✓ Finished streaming.")
    full_response = "".join(stream_output)
    
    # Assertions
    assert len(full_response) > 0, "Response stream was empty"
    print("✓ Output verified successfully.")

    # Test streaming for 'transportation' agent
    print("\nTesting streaming response for 'transportation' agent...")
    stream_output_trans = []
    async for chunk in gemini_agent_service.chat_stream(
        agent_id="transportation",
        message="Are there any delayed shuttles right now?",
    ):
        sys.stdout.write(chunk)
        sys.stdout.flush()
        stream_output_trans.append(chunk)
        
    print("\n\n✓ Finished streaming.")
    full_response_trans = "".join(stream_output_trans)
    assert len(full_response_trans) > 0, "Response stream was empty"
    print("✓ Output verified successfully.")

    print("\nAll 8 Gemini Copilot Agents verified successfully!")

if __name__ == "__main__":
    asyncio.run(test_gemini_agents())
