# src/api/dependencies.py
from fastapi import Request
from src.services.semantic_router import SemanticToolRouter
from src.services.llm_service import LLMService

def get_semantic_router(request: Request) -> SemanticToolRouter:
    # 从 FastAPI app 状态中获取全局单例
    return request.app.state.semantic_router

def get_llm_service() -> LLMService:
    return LLMService()