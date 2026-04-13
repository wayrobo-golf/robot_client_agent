from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # 基础配置
    APP_NAME: str = "GolfRobotAgent"
    APP_ID: str = "golf-agent-01"
    
    # 本地 vLLM 配置 (对应你 start_vllm.sh 中的 8001 端口)
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_API_KEY: str = "sk-your-real-key"
    LLM_MODEL_NAME: str = "deepseek-chat"
    
    # Redis 存储配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6380
    
    # 语义路由配置
    EMBED_MODEL_PATH: str = "BAAI/bge-small-zh-v1.5"
    
    # 支持从 .env 文件读取
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# 实例化单例
settings = Settings()