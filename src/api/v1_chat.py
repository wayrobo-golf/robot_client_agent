# src/api/v1_chat.py
from fastapi import APIRouter, Depends, HTTPException
import logging

from src.models.schemas import ChatRequest, ChatResponse, AgentDecision
from src.services.semantic_router import SemanticToolRouter
from src.services.llm_service import LLMService
from src.api.dependencies import get_semantic_router, get_llm_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    semantic_router: SemanticToolRouter = Depends(get_semantic_router),
    llm_service: LLMService = Depends(get_llm_service),
    memory: MemoryService = Depends(get_memory_service) # 注入记忆服务
):
    try:
        # 1. 获取该用户对该机器人的历史记忆
        history = memory.get_history(request.user_id, request.robot_id)
        
        # 2. 动态路由
        active_tools = semantic_router.get_final_prompt_tools(request.text)
        
        # 3. 推理决策 (传入历史)
        decision = await llm_service.generate_decision(
            system_prompt=SYSTEM_PROMPT_TEMPLATE,
            user_text=request.text,
            active_tools=active_tools,
            history=history 
        )
        
        # 4. 【关键】更新记忆：存入用户的这句，和模型的回复这句
        memory.add_message(request.user_id, request.robot_id, "user", request.text)
        memory.add_message(request.user_id, request.robot_id, "assistant", decision.reply_to_user)
        
        return ChatResponse(tts_text=decision.reply_to_user, ...)

    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="中枢系统内部错误")