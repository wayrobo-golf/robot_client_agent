# src/api/v1_chat.py
from fastapi import APIRouter, Depends, HTTPException
import logging

from src.models.schemas import ChatRequest, ChatResponse
from src.services.semantic_router import SemanticToolRouter
from src.services.llm_service import LLMService
from src.api.dependencies import get_semantic_router, get_llm_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    semantic_router: SemanticToolRouter = Depends(get_semantic_router),
    llm_service: LLMService = Depends(get_llm_service)
):
    try:
        active_tools = semantic_router.get_final_prompt_tools(
            query=request.text, 
            top_k=2, 
            threshold=0.55
        )
        
        robot_state = "电量 65%，状态空闲。"
        system_prompt = f"你是一个高尔夫球场捡球机器人中枢。当前状态：{robot_state}"
        
        reply_text = await llm_service.generate_action(system_prompt, request.text, active_tools)
        
        tool_names_for_debug = [t['function']['name'] for t in active_tools]
        
        return ChatResponse(
            tts_text=f"已受理指令。激活模块：{', '.join(tool_names_for_debug)}。{reply_text}",
            active_tools=tool_names_for_debug
        )
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")