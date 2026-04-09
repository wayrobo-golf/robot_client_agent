# src/api/dependencies.py
from fastapi import Request
from src.services.semantic_router import SemanticToolRouter
from src.services.llm_service import LLMService
from src.services.memory_service import MemoryService

def get_semantic_router(request: Request) -> SemanticToolRouter:
    # 从 FastAPI app 状态中获取全局单例
    return request.app.state.semantic_router

def get_llm_service() -> LLMService:
    return LLMService()

# 全局单例，通常在 main.py 初始化后挂载
def get_memory_service(request: Request) -> MemoryService:
    return request.app.state.memory_service