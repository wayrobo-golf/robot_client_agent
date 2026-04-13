# src/services/llm_service.py
import logging
import json
import re
from typing import List, Dict, Optional
from openai import AsyncOpenAI, APIError
from pydantic import ValidationError

from src.models.schemas import AgentDecision

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, base_url: str = "http://localhost:8000/v1", api_key: str = "EMPTY", model_name: str = "Qwen/Qwen2.5-7B-Instruct"):
        """
        初始化大模型服务
        :param base_url: vLLM 的服务地址
        :param api_key: vLLM 默认不需要鉴权，填 EMPTY 即可
        :param model_name: 启动 vLLM 时注册的模型名称
        """
        # api_key = "sk-973b01b0a20040bab25fcd8c726099c7"
        # base_url = "https://api.deepseek.com/v1"
        # model_name = "deepseek-chat"
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name
        logger.info(f"LLM Service 初始化完成，指向: {base_url}, 模型: {model_name}")

    def _inject_tools_into_prompt(self, base_system_prompt: str, active_tools: list) -> str:
        """
        格式化并注入当前可用的工具指令到 System Prompt 中。
        采用极度严厉的指令，抑制大模型的聊天废话。
        """
        tools_str = json.dumps(active_tools, ensure_ascii=False, indent=2) if active_tools else "当前无可用控制指令。"
        
        target_schema = {
            "thought_process": "在这里写下你的逻辑思考过程（必填）",
            "tasks": [
                {
                    "action_name": "必须是从上方【可用控制指令】中选出的 name",
                    "parameters": {"参数1": "值1"}
                }
            ],
            "reply_to_user": "最终要用语音播报给用户的中文回复（必填）"
        }

        full_prompt = (
            f"{base_system_prompt}\n\n"
            f"=== 当前可用控制指令 (Tools) ===\n{tools_str}\n\n"
            f"=== 🛑 绝对强制指令 ===\n"
            f"你现在是一个机器人的底层控制程序（API），不是聊天助手！\n"
            f"禁止输出任何多余的问候语（如“好的”、“检测到”、“正在调用”）。\n"
            f"你必须且只能输出一段纯 JSON，格式必须完全符合以下结构：\n"
            f"{json.dumps(target_schema, ensure_ascii=False, indent=2)}"
        )
        return full_prompt

    def _extract_json_from_text(self, raw_text: str) -> str:
        """
        核心清理逻辑：从混杂了 Markdown 标记或废话的文本中，暴力提取有效 JSON。
        """
        cleaned = raw_text.strip()
        
        # 使用 `{3}` 代替连续的反引号，避免 Markdown 解析引擎误判截断
        json_match = re.search(r'`{3}(?:json)?(.*?)`{3}', cleaned, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()
            
        # 备用方案：强行截取第一个 { 和最后一个 } 之间的内容
        start_idx = cleaned.find('{')
        end_idx = cleaned.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return cleaned[start_idx:end_idx+1].strip()
            
        return cleaned

    async def generate_decision(
        self, 
        system_prompt: str, 
        user_text: str, 
        active_tools: list, 
        history: Optional[List[Dict[str, str]]] = None
    ) -> AgentDecision:
        """
        核心业务方法：发送请求、提取 JSON 并校验反序列化。
        """
        full_system_prompt = self._inject_tools_into_prompt(system_prompt, active_tools)
        
        messages = [{"role": "system", "content": full_system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_text})

        try:
            logger.info("正在请求云端大模型推理...")
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"} 
            )

            raw_output = response.choices[0].message.content
            logger.debug(f"LLM 原始输出:\n{raw_output}")

            cleaned_output = self._extract_json_from_text(raw_output)
            
            final_decision = AgentDecision.model_validate_json(cleaned_output)
            logger.info(f"大模型决策成功: 包含 {len(final_decision.tasks)} 个动作")
            return final_decision

        except ValidationError as ve:
            logger.error(f"LLM 输出字段校验失败: {ve}\n清理文本: {cleaned_output if 'cleaned_output' in locals() else 'None'}\n原始输出: {raw_output if 'raw_output' in locals() else 'None'}")
            return self._fallback_decision("抱歉，我生成的控制指令不符合规范，无法执行。")
            
        except APIError as ae:
            logger.error(f"大模型 API 请求失败 (APIError): {ae}")
            return self._fallback_decision("抱歉，我与中央计算大脑失去了连接。")
            
        except Exception as e:
            logger.error(f"云端大模型请求或解析遇到未知异常: {e}", exc_info=True)
            return self._fallback_decision("抱歉，我的逻辑解析模块遇到了内部错误。")

    def _fallback_decision(self, error_message: str) -> AgentDecision:
        """
        系统降级/异常兜底策略。
        """
        return AgentDecision(
            thought_process="系统出现异常，已触发安全兜底机制。",
            tasks=[], 
            reply_to_user=error_message
        )