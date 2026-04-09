# src/services/memory_service.py
import json
import redis
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class MemoryService:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, ttl: int = 1800):
        """
        :param ttl: 过期时间，默认 1800 秒 (30分钟)
        """
        self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.ttl = ttl

    def _get_key(self, user_id: str, robot_id: str) -> str:
        return f"chat_history:{user_id}:{robot_id}"

    def get_history(self, user_id: str, robot_id: str, max_turns: int = 10) -> List[Dict[str, str]]:
        """获取最近 N 条对话记录"""
        key = self._get_key(user_id, robot_id)
        # 从列表右侧获取最新的记录
        history_raw = self.redis_client.lrange(key, -max_turns, -1)
        return [json.loads(m) for m in history_raw]

    def add_message(self, user_id: str, robot_id: str, role: str, content: str):
        """存储单条消息"""
        key = self._get_key(user_id, robot_id)
        message = {"role": role, "content": content}
        
        # 将新消息推入列表右侧
        self.redis_client.rpush(key, json.dumps(message, ensure_ascii=False))
        # 刷新过期时间
        self.redis_client.expire(key, self.ttl)
        
        # 保持列表长度，防止无限增长 (只保留最近 20 条消息)
        self.redis_client.ltrim(key, -20, -1)

    def clear_history(self, user_id: str, robot_id: str):
        self.redis_client.delete(self._get_key(user_id, robot_id))