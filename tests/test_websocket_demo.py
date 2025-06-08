#!/usr/bin/env python3
"""
Simple WebSocket demo for the Healf wellness profiling platform.
This script demonstrates the real-time conversational interface.
"""

import asyncio
import websockets
import json
import sys
import pytest
from websockets.exceptions import ConnectionClosed, InvalidURI

async def wellness_chat_demo():
    """Demo the wellness chat functionality"""
    uri = "ws://localhost:8000/ws/demo_user_123"
    
    print("🌟 Healf Wellness Profiling Demo")
    print("=" * 40)
    print("Connecting to wellness profiling platform...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected! Starting wellness profile creation...\n")
            
            # Receive initial question
            response = await websocket.recv()
            message = json.loads(response)
            
            if message['type'] == 'INIT_PROFILE':
                question_data = message['data']
                if question_data['type'] == 'question':
                    print(f"🤖 Assistant: {question_data['question']}")
                    
                    # Simulate user responses
                    demo_responses = [
                        "I'm 28 years old",
                        "I'm female", 
                        "I exercise regularly, about 4 times a week",
                        "I'm vegetarian",
                        "I sleep pretty well, usually 7-8 hours",
                        "My stress level is moderate",
                        "I want to improve my overall fitness and energy levels"
                    ]
                    
                    for i, user_answer in enumerate(demo_responses):
                        print(f"👤 You: {user_answer}")
                        
                        # Send answer with proper context
                        answer_message = {
                            "type": "USER_ANSWER",
                            "data": {
                                "answer": user_answer,
                                "context": {
                                    "field": question_data.get('field', 'general')
                                }
                            }
                        }
                        await websocket.send(json.dumps(answer_message))
                        
                        # Receive next question or completion
                        response = await websocket.recv()
                        message = json.loads(response)
                        
                        if message['type'] == 'ASSISTANT_QUESTION':
                            question_data = message['data']
                            print(f"\n🤖 Assistant: {question_data['question']}")
                        elif message['type'] == 'PROFILE_COMPLETE':
                            completion_data = message['data']
                            print(f"\n🎉 {completion_data['message']}")
                            print("\n📊 Your completed wellness profile:")
                            profile = completion_data['profile']
                            print(f"   Age: {profile.get('age', 'Not set')}")
                            print(f"   Gender: {profile.get('gender', 'Not set')}")
                            print(f"   Activity Level: {profile.get('activity_level', 'Not set')}")
                            print(f"   Dietary Preference: {profile.get('dietary_preference', 'Not set')}")
                            print(f"   Sleep Quality: {profile.get('sleep_quality', 'Not set')}")
                            print(f"   Stress Level: {profile.get('stress_level', 'Not set')}")
                            print(f"   Health Goals: {profile.get('health_goals', 'Not set')}")
                            print(f"   Completion: {profile.get('completion_percentage', 0):.1f}%")
                            break
                        elif message['type'] == 'ERROR':
                            print(f"\n❌ Error: {message['data'].get('message', 'Unknown error')}")
                            break
                        
                        # Small delay for demo effect
                        await asyncio.sleep(1)
                        
                        if i >= len(demo_responses) - 1:
                            break
            
            return True
    
    except ConnectionClosed:
        print("❌ Connection was closed unexpectedly")
        return False
    except ConnectionRefusedError:
        print("❌ Could not connect to server. Is the server running on localhost:8000?")
        return False
    except OSError as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

@pytest.mark.asyncio
async def test_websocket_demo():
    """Pytest-compatible version of the WebSocket demo"""
    # Since this test requires a running server, we'll skip it during automated testing
    # but allow it to run manually when the server is available
    
    try:
        success = await asyncio.wait_for(wellness_chat_demo(), timeout=5.0)
        # If we get here, the server was running and the test succeeded
        assert success
    except (ConnectionRefusedError, OSError, asyncio.TimeoutError):
        # Server not running, skip the test
        pytest.skip("WebSocket server not running - skipping integration test")
    except Exception as e:
        # Other errors should fail the test
        pytest.fail(f"WebSocket test failed with unexpected error: {e}")

# Allow running the demo standalone
if __name__ == "__main__":
    print("Running WebSocket Demo...")
    print("Make sure the server is running: uvicorn app.main:app --reload")
    print()
    
    asyncio.run(wellness_chat_demo()) 