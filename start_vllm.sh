#!/bin/bash

# 建议模型：Qwen2.5-7B-Instruct (对中文和指令遵循效果极佳)
MODEL_PATH="Qwen/Qwen2.5-7B-Instruct"

# 镜像版本：v0.5.4 是兼容 CUDA 12.2 (驱动 535) 较为稳定的版本
VLLM_VERSION="v0.5.4"

echo "正在清理旧的 vLLM 容器..."
docker stop vllm-server 2>/dev/null
docker rm -f vllm-server 2>/dev/null

docker run -d --gpus all \
    -p 8000:8000 \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --name vllm-server \
    vllm/vllm-openai:$VLLM_VERSION \
    --model $MODEL_PATH \
    --served-model-name qwen2.5-7b \
    --max-model-len 8192 \
    --dtype float16 \
    --enforce-eager
    
echo "启动指令已发出。请执行 'docker logs -f vllm-server' 查看加载进度。"