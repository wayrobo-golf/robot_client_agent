# src/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

from src.core.config import ROBOT_TOOLS_REGISTRY, STATIC_TOOL_NAMES
from src.services.semantic_router import SemanticToolRouter
from src.api.v1_chat import router as chat_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("App")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing dependencies...")
    # 将 router 实例挂载到 app.state，实现全局单例，避免重复加载模型
    app.state.semantic_router = SemanticToolRouter(
        tools_data=ROBOT_TOOLS_REGISTRY, 
        static_tool_names=STATIC_TOOL_NAMES
    )
    logger.info("Application ready.")
    yield
    logger.info("Application shutting down.")

app = FastAPI(title="Robot Agent API", lifespan=lifespan)

# 注册 API 路由
app.include_router(chat_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)