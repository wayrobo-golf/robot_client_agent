# src/api/dependencies.py
from fastapi import Request
from src.services.semantic_router import SemanticToolRouter
from src.services.llm_service import LLMService
from src.services.memory_service import MemoryService
from config.config import settings

def get_semantic_router(request: Request) -> SemanticToolRouter:
    # 从 FastAPI app 状态中获取全局单例
    return request.app.state.semantic_router

# 单例模式确保全局共享同一个客户端连接池
_llm_service = None

def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        # 显式将配置传入构造函数，实现解耦
        _llm_service = LLMService(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            model_name=settings.LLM_MODEL_NAME
        )
    return _llm_service

# 全局单例，通常在 main.py 初始化后挂载
def get_memory_service(request: Request) -> MemoryService:
    return request.app.state.memory_service