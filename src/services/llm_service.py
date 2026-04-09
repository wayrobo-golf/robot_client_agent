# src/services/llm_service.py
import logging
import json
from openai import AsyncOpenAI, APIError
from pydantic import ValidationError

from src.models.schemas import AgentDecision, ActionCall

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, base_url: str = "http://localhost:8000/v1", api_key: str = "EMPTY", model_name: str = "Qwen/Qwen2.5-7B-Instruct"):
        """
        初始化大模型服务
        :param base_url: vLLM 的服务地址
        :param api_key: vLLM 默认不需要鉴权，填 EMPTY 即可
        :param model_name: 启动 vLLM 时注册的模型名称
        """
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name
        logger.info(f"LLM Service 初始化完成，指向: {base_url}, 模型: {model_name}")

    def _inject_tools_into_prompt(self, base_system_prompt: str, active_tools: list) -> str:
        """
        将动态路由筛选出的工具，格式化并注入到 System Prompt 中
        这样模型就知道当前能用哪些动作，以及参数长什么样。
        """
        if not active_tools:
            tools_str = "当前无可用控制模块。"
        else:
            # 将 JSON Schema 转为美观的字符串供大模型阅读
            tools_str = json.dumps(active_tools, ensure_ascii=False, indent=2)

        # 拼装最终的系统提示词
        full_prompt = (
            f"{base_system_prompt}\n\n"
            f"=== 当前已激活的机器人控制指令 (Tools) ===\n"
            f"{tools_str}\n\n"
            f"⚠️ 注意：如果你需要控制机器人执行动作，请严格从上述列表中选择 `action_name`，"
            f"并参照 `parameters` 的要求提取参数。"
        )
        return full_prompt

    async def generate_decision(self, system_prompt: str, user_text: str, active_tools: list) -> AgentDecision:
        """
        核心推理函数：发送请求并执行约束解码
        """
        # 1. 组装终极 Prompt
        full_system_prompt = self._inject_tools_into_prompt(system_prompt, active_tools)
        
        # 2. 提取强制输出约束 Schema
        guided_schema = AgentDecision.model_json_schema()

        try:
            logger.info("正在请求大模型推理...")
            
            # 3. 发送异步请求
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": full_system_prompt},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.1, # 设定极低温度，保证逻辑严谨和控制指令的确定性
                # 【核心魔法】：将 Schema 塞给 vLLM 底层的 outlines 引擎
                extra_body={"guided_json": guided_schema}
            )

            # 4. 获取模型吐出的字符串 (此时能保证在语法层面100%是合法的JSON)
            raw_output = response.choices[0].message.content
            logger.debug(f"LLM 原始输出: {raw_output}")

            # 5. 使用 Pydantic 进行严格反序列化和业务校验
            final_decision = AgentDecision.model_validate_json(raw_output)
            
            logger.info(f"大模型决策成功: 包含 {len(final_decision.tasks)} 个动作")
            return final_decision

        except ValidationError as ve:
            # 物理层面 JSON 是对的，但业务逻辑层面填错了（比如 action_name 瞎编的）
            logger.error(f"LLM 输出字段校验失败: {ve}\nRaw Output: {raw_output}")
            return self._fallback_decision("抱歉，系统内部逻辑校验失败，请稍后再试。")
            
        except APIError as ae:
            # vLLM 服务器挂了，或者网络不通
            logger.error(f"大模型 API 请求失败: {ae}")
            return self._fallback_decision("抱歉，我与中央计算大脑失去了连接。")
            
        except Exception as e:
            # 兜底异常
            logger.error(f"未知推理异常: {e}")
            return self._fallback_decision("抱歉，我的思维模块遇到了未知故障。")

    def _fallback_decision(self, error_message: str) -> AgentDecision:
        """
        故障兜底策略：当大模型崩溃时，确保不会返回空指针让底盘死机，
        而是生成一个安全的空动作，并向用户播报错误。
        """
        return AgentDecision(
            thought_process="系统出现异常，拦截错误。",
            tasks=[], 
            reply_to_user=error_message
        )