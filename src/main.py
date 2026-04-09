# src/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

from src.core.config import ROBOT_TOOLS_REGISTRY, STATIC_TOOL_NAMES
from src.services.semantic_router import SemanticToolRouter
from src.services.memory_service import MemoryService
from src.api.v1_chat import router as chat_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("App")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 正在初始化中枢系统依赖...")
    
    # 1. 初始化并挂载语义路由服务 (耗时操作，仅执行一次)
    logger.info("-> 加载向量检索模型...")
    app.state.semantic_router = SemanticToolRouter(
        tools_data=ROBOT_TOOLS_REGISTRY, 
        static_tool_names=STATIC_TOOL_NAMES
    )
    
    # 2. 初始化并挂载 Redis 记忆服务 (新增模块)
    logger.info("-> 连接 Redis 记忆数据库...")
    try:
        # 这里可以替换为从环境变量读取配置
        memory_service = MemoryService(host="localhost", port=6379, db=0)
        
        # 启动时执行健康检查 (Ping)
        memory_service.redis_client.ping()
        app.state.memory_service = memory_service
        logger.info("✅ Redis 连接成功，记忆模块已就绪。")
        
    except Exception as e:
        logger.error(f"❌ Redis 连接失败，请检查 Redis 服务是否启动！错误信息: {e}")
        # 在严谨的生产环境中，如果核心中间件连不上，可以考虑直接 raise e 阻止系统启动
        raise RuntimeError("系统启动失败：缺失核心 Redis 依赖") from e

    logger.info("✨ 高尔夫机器人中枢 Application 准备就绪。")
    yield
    
    # --- 服务关闭时的清理工作 ---
    logger.info("🛑 正在关闭系统，释放资源...")
    if hasattr(app.state, "memory_service"):
        app.state.memory_service.redis_client.close()
        logger.info("Redis 连接已安全断开。")

# 初始化 FastAPI 应用
app = FastAPI(title="Golf Robot Agent API", version="1.0.0", lifespan=lifespan)

# 注册 API 路由
app.include_router(chat_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    # 启动命令: python -m src.main (或者使用 uv run)
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)