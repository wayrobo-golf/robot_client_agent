# src/models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# ==========================================
# 第一部分：APP 与后端的 HTTP 交互接口
# ==========================================

class RobotState(BaseModel):
    """当前机器人的硬件状态（通常由 APP 或底盘随请求附带上报）"""
    battery: int = Field(..., ge=0, le=100, description="当前电量百分比")
    is_charging: bool = Field(..., description="是否正在充电")
    current_location: str = Field(..., description="当前所在区域，如'A区', '充电桩', '沙坑'")
    basket_capacity: int = Field(..., ge=0, le=100, description="球篓已装载的百分比")
    hardware_status: str = Field(default="normal", description="硬件状态，如 normal, stuck(卡住), error")

class ChatRequest(BaseModel):
    """手机 APP 发给后端的语音指令请求"""
    user_id: str = Field(..., description="用户ID，用于多轮对话的上下文隔离")
    robot_id: str = Field(..., description="目标机器人设备编号")
    text: str = Field(..., description="用户语音识别后的文本指令")
    state: RobotState = Field(..., description="机器人的实时状态数据")

class ChatResponse(BaseModel):
    """后端处理完毕后，返回给手机 APP 的响应"""
    tts_text: str = Field(..., description="APP端需要立即转化为语音播报给用户的文本")
    # 可选：如果需要在 APP 界面上展示当前触发了什么动作，可以返回这个字段
    executed_actions: List[str] = Field(default_factory=list, description="本次执行的核心动作名称列表")


# ==========================================
# 第二部分：大模型 (LLM) 内部输出的强制约束结构
# ==========================================
# 这里的模型不是用来处理 HTTP 请求的，而是用来“规训”大模型的。

class ActionCall(BaseModel):
    """大模型决定的单次动作调用"""
    action_name: str = Field(..., description="工具的名称，例如 start_collecting, emergency_stop")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="执行该动作所需的具体参数，如 {'zone_name': 'A区'}")

class AgentDecision(BaseModel):
    """大模型最终必须输出的终极 JSON 结构"""
    
    # 1. 强制思维链 (Chain of Thought)
    # 让模型在给出动作前，先强制写一段内心OS，分析当前状态和用户意图。这能极大降低逻辑错误！
    thought_process: str = Field(
        ..., 
        description="内部思考过程：请分析用户的意图，并结合当前机器人的状态（电量、位置、容量），思考应该调用哪些动作，或者是否需要追问用户。"
    )
    
    # 2. 动作序列
    # 允许模型一次性输出多个动作（例如：先脱困，再重新建图，最后回充）
    tasks: List[ActionCall] = Field(
        default_factory=list, 
        description="需要机器人底层执行的任务列表。如果不需要执行动作（如仅仅是日常寒暄或追问用户），此列表为空 []"
    )
    
    # 3. 语音回复
    reply_to_user: str = Field(
        ..., 
        description="这是你作为高尔夫球场智能中枢，直接回复给用户的语音文本。语气要专业、简洁。"
    )