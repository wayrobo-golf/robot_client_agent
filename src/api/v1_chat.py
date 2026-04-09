# src/api/v1_chat.py
from fastapi import APIRouter, Depends, HTTPException
import logging

from src.models.schemas import ChatRequest, ChatResponse, AgentDecision
from src.services.semantic_router import SemanticToolRouter
from src.services.llm_service import LLMService
from src.services.memory_service import MemoryService  # 新增：导入 MemoryService 类型
from src.api.dependencies import get_semantic_router, get_llm_service, get_memory_service # 新增：导入 get_memory_service 方法

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
        
        # 2. 动态路由：筛选最相关的工具
        active_tools = semantic_router.get_final_prompt_tools(
            query=request.text, 
            top_k=2, 
            threshold=0.55
        )
        
        # 3. 组装包含机器人实时状态的 System Prompt
        robot_state = f"电量 {request.state.battery}%, 正在充电: {request.state.is_charging}, 位置: {request.state.current_location}, 球篓容量: {request.state.basket_capacity}%, 硬件状态: {request.state.hardware_status}。"
        
        system_prompt = f"""你是一个高尔夫球场智能捡球机器人中枢Agent。
【你的任务】
分析用户的语音指令，结合当前机器人状态，决定下一步的动作。
如果你觉得当前状态无法执行用户指令（例如没电了却被要求去干活），你需要向用户解释原因。

【当前机器人状态】
{robot_state}
"""
        
        # 4. 推理决策 (传入提示词、用户输入、工具以及历史记忆)
        decision = await llm_service.generate_decision(
            system_prompt=system_prompt,
            user_text=request.text,
            active_tools=active_tools,
            history=history 
        )
        
        # 5. 更新记忆：存入用户的这句，和模型的回复这句
        memory.add_message(request.user_id, request.robot_id, "user", request.text)
        memory.add_message(request.user_id, request.robot_id, "assistant", decision.reply_to_user)
        
        # 6. 提取准备下发给机器人的动作列表名称
        executed_action_names = [task.action_name for task in decision.tasks]
        
        # 7. 组装合法的响应并返回
        return ChatResponse(
            tts_text=decision.reply_to_user,
            executed_actions=executed_action_names
        )

    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="中枢系统内部错误")