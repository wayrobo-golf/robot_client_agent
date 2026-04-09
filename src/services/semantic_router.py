# src/services/semantic_router.py
import logging
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class SemanticToolRouter:
    """高内聚：只负责向量化计算和工具过滤匹配"""
    
    def __init__(self, tools_data: list[dict], static_tool_names: list[str], model_path: str = 'BAAI/bge-small-zh-v1.5'):
        self.tools_data = tools_data
        self.static_tool_names = static_tool_names
        
        logger.info(f"Loading embedding model: {model_path}")
        self.embed_model = SentenceTransformer(model_path, device='cpu')
        
        self.tool_vectors = None
        self._build_index()

    def _build_index(self) -> None:
        texts_to_embed = [
            f"功能: {t['description']} 关键词: {' '.join(t.get('search_keywords', []))}"
            for t in self.tools_data
        ]
        self.tool_vectors = self.embed_model.encode(
            texts_to_embed, 
            normalize_embeddings=True,
            show_progress_bar=False
        )

    def _format_for_llm(self, tool_dict: dict) -> dict:
        return {
            "type": "function",
            "function": {
                "name": tool_dict["name"],
                "description": tool_dict["description"],
                "parameters": tool_dict["parameters"]
            }
        }

    def get_final_prompt_tools(self, query: str, top_k: int = 2, threshold: float = 0.50) -> list[dict]:
        if not query:
            return []

        query_vector = self.embed_model.encode([query], normalize_embeddings=True)[0]
        scores = np.dot(self.tool_vectors, query_vector)
        
        candidate_indices = np.where(scores >= threshold)[0]
        top_indices = candidate_indices[np.argsort(scores[candidate_indices])[::-1][:top_k]]
        
        final_tools_map = {}
        for idx in top_indices:
            tool = self.tools_data[idx]
            final_tools_map[tool["name"]] = self._format_for_llm(tool)

        for tool in self.tools_data:
            if tool["name"] in self.static_tool_names and tool["name"] not in final_tools_map:
                final_tools_map[tool["name"]] = self._format_for_llm(tool)

        return list(final_tools_map.values())