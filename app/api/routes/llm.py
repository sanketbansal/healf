from fastapi import APIRouter
from typing import Dict, Any
from app.dao.llm_dao import get_llm_dao

router = APIRouter(prefix="/llm", tags=["llm"])

@router.get("/status")
async def llm_status_check() -> Dict[str, Any]:
    """Check the status of LLM providers"""
    llm_dao = get_llm_dao()
    return await llm_dao.get_provider_status() 