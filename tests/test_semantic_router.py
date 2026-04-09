# tests/test_semantic_router.py
import pytest
from src.services.semantic_router import SemanticToolRouter

# 准备测试桩数据 (Mock Data)
MOCK_TOOLS = [
    {
        "id": "t1", "name": "start_collecting", 
        "description": "捡球", "parameters": {}, "search_keywords": ["干活"]
    },
    {
        "id": "t2", "name": "emergency_stop", 
        "description": "急停", "parameters": {}, "search_keywords": ["停"]
    }
]

@pytest.fixture(scope="module")
def router_instance():
    # 测试时可以替换为更小的模型或直接返回实例
    return SemanticToolRouter(tools_data=MOCK_TOOLS, static_tool_names=["emergency_stop"])

def test_static_tools_always_included(router_instance):
    # 即便输入无关词汇，常驻工具也必须被召回
    result = router_instance.get_final_prompt_tools("今天天气怎么样", top_k=1, threshold=0.99)
    names = [t['function']['name'] for t in result]
    
    assert "emergency_stop" in names
    assert len(names) == 1

def test_dynamic_tool_matching(router_instance):
    # 明确的指令应召回对应的工具
    result = router_instance.get_final_prompt_tools("去捡球干活", top_k=1, threshold=0.1)
    names = [t['function']['name'] for t in result]
    
    assert "start_collecting" in names
    assert "emergency_stop" in names # 常驻工具依然存在