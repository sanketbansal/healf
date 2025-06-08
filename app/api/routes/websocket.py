from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.dao.websocket_dao import WebSocketDAO
from app.dao.profile_dao import ProfileDAO
from app.dao.llm_dao import LLMDao
from app.services.profile_service import ProfileService
from app.services.question_service import QuestionService
import json
from datetime import datetime

router = APIRouter()

# Initialize DAOs
websocket_dao = WebSocketDAO()
profile_dao = ProfileDAO()
llm_dao = LLMDao()

# Initialize services with DAO dependencies
profile_service = ProfileService(profile_dao)
question_service = QuestionService(llm_dao)

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    await websocket_dao.connect_user(user_id, websocket)
    
    try:
        # Initialize or get existing profile
        profile = await profile_service.get_or_create_profile(user_id)
        
        # Generate first question
        question_response = await question_service.generate_next_question(profile)
        
        # Send initial message
        await websocket.send_text(json.dumps({
            "type": "INIT_PROFILE",
            "data": question_response,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "USER_ANSWER":
                response = await process_user_answer(user_id, message["data"])
                await websocket.send_text(json.dumps(response))
                
    except WebSocketDisconnect:
        await websocket_dao.disconnect_user(user_id)
    except Exception as e:
        # Send error message and close connection
        await websocket.send_text(json.dumps({
            "type": "ERROR",
            "data": {"message": f"An error occurred: {str(e)}"},
            "timestamp": datetime.utcnow().isoformat()
        }))
        await websocket_dao.disconnect_user(user_id)

async def process_user_answer(user_id: str, answer_data: dict):
    """Process user answer using the question service"""
    
    try:
        # Process the answer
        processed_answer = question_service.process_user_answer(
            answer_data['answer'], 
            answer_data.get('context', {})
        )
        
        # Update profile
        profile = await profile_service.update_profile(user_id, {
            processed_answer['field']: processed_answer['value']
        })
        
        # Generate next question
        next_question = await question_service.generate_next_question(profile)
        
        if next_question['type'] == 'completion':
            return {
                "type": "PROFILE_COMPLETE", 
                "data": next_question,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "type": "ASSISTANT_QUESTION",
                "data": next_question,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    except Exception as e:
        return {
            "type": "ERROR",
            "data": {"message": f"Error processing answer: {str(e)}"},
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket and LLM usage statistics"""
    stats = await websocket_dao.get_connection_statistics()
    return {
        "active_connections": stats.get("active_connections", 0),
        "total_sessions": stats.get("total_connections", 0),
        "peak_connections": stats.get("peak_connections", 0),
        "last_updated": stats.get("last_updated")
    } 