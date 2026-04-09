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
    llm_service: LLMService = Depends(get_llm_service)
):
    try:
        # 1. 动态工具路由 (从 17 个指令中捞出最相关的)
        active_tools = semantic_router.get_final_prompt_tools(
            query=request.text, 
            top_k=2, 
            threshold=0.55
        )
        
        # 2. 组装包含机器人实时状态的 System Prompt
        # request.state 是我们在 schemas 里定义的 RobotState
        robot_state = f"电量 {request.state.battery}%, 正在充电: {request.state.is_charging}, 位置: {request.state.current_location}, 球篓容量: {request.state.basket_capacity}%, 硬件状态: {request.state.hardware_status}。"
        
        system_prompt = f"""你是一个高尔夫球场智能捡球机器人中枢Agent。
【你的任务】
分析用户的语音指令，结合当前机器人状态，决定下一步的动作。
如果你觉得当前状态无法执行用户指令（例如没电了却被要求去干活），你需要向用户解释原因。

【当前机器人状态】
{robot_state}
"""
        
        # 3. 呼叫大模型服务进行约束解码
        decision: AgentDecision = await llm_service.generate_decision(
            system_prompt=system_prompt,
            user_text=request.text,
            active_tools=active_tools
        )
        
        # --- 这里可以插入一段异步代码，将 decision.tasks 发送给 ROS2 的 MQTT Broker ---
        # async_send_to_ros2(request.robot_id, decision.tasks)
        
        # 4. 组装给 APP 的最终返回
        executed_action_names = [task.action_name for task in decision.tasks]
        
        return ChatResponse(
            tts_text=decision.reply_to_user,
            executed_actions=executed_action_names
        )

    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="中枢系统内部错误")