#!/bin/bash
set -euo pipefail

# 建议模型：Qwen2.5-7B-Instruct (对中文和指令遵循效果极佳)
MODEL_PATH="Qwen/Qwen2.5-7B-Instruct"

# 镜像版本：v0.8.5（配合 compat 目录屏蔽可规避 Error 804）
VLLM_VERSION="v0.8.5"

# 可通过环境变量覆盖镜像源；若镜像源不稳定可切回官方 https://huggingface.co
HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
HF_ENDPOINT_FALLBACK="https://hf-mirror.com"

# 增大 HuggingFace 元数据和文件下载超时，避免 read timeout=10 导致启动失败
HF_HUB_ETAG_TIMEOUT="${HF_HUB_ETAG_TIMEOUT:-60}"
HF_HUB_DOWNLOAD_TIMEOUT="${HF_HUB_DOWNLOAD_TIMEOUT:-1800}"

# 端口与就绪探测参数
HOST_PORT="${HOST_PORT:-8001}"
CONTAINER_PORT="${CONTAINER_PORT:-8000}"
READY_TIMEOUT_SECONDS="${READY_TIMEOUT_SECONDS:-900}"

# 代理变量透传（如果宿主机已开启代理）
HTTP_PROXY="${HTTP_PROXY:-}"
HTTPS_PROXY="${HTTPS_PROXY:-}"
ALL_PROXY="${ALL_PROXY:-}"
NO_PROXY="${NO_PROXY:-}"

CACHE_DIR="${HOME}/.cache/huggingface"
MODEL_CACHE_DIR="${CACHE_DIR}/hub/models--Qwen--Qwen2.5-7B-Instruct"

check_url_reachable() {
    local url="$1"
    curl -fsSI --max-time 8 "$url" >/dev/null 2>&1
}

echo "正在清理旧的 vLLM 容器..."
docker stop vllm-server 2>/dev/null
docker rm -f vllm-server 2>/dev/null

if [ -d "${MODEL_CACHE_DIR}" ]; then
    # 上一次异常中断可能残留 .incomplete 文件，清理后可避免反复卡在损坏缓存
    find "${MODEL_CACHE_DIR}" -type f -name "*.incomplete" -print -delete || true
fi

# 如果用户显式或隐式使用了不可达端点，自动回退到可达镜像源
if ! check_url_reachable "${HF_ENDPOINT}"; then
    echo "警告: 当前 HF_ENDPOINT 不可达 -> ${HF_ENDPOINT}"
    if [ "${HF_ENDPOINT}" != "${HF_ENDPOINT_FALLBACK}" ] && check_url_reachable "${HF_ENDPOINT_FALLBACK}"; then
        echo "自动切换到可达镜像源: ${HF_ENDPOINT_FALLBACK}"
        HF_ENDPOINT="${HF_ENDPOINT_FALLBACK}"
    else
        echo "错误: 无可用模型下载端点，请检查网络/代理后重试。"
        echo "可尝试: export HF_ENDPOINT=https://hf-mirror.com"
        exit 1
    fi
fi

echo "使用模型下载端点: ${HF_ENDPOINT}"

docker run -d --gpus all \
    -p ${HOST_PORT}:${CONTAINER_PORT} \
    --runtime=nvidia \
    --mount type=tmpfs,destination=/usr/local/cuda/compat \
    -e HF_ENDPOINT=${HF_ENDPOINT} \
    -e HF_HUB_ETAG_TIMEOUT=${HF_HUB_ETAG_TIMEOUT} \
    -e HF_HUB_DOWNLOAD_TIMEOUT=${HF_HUB_DOWNLOAD_TIMEOUT} \
    -e HTTP_PROXY=${HTTP_PROXY} \
    -e HTTPS_PROXY=${HTTPS_PROXY} \
    -e ALL_PROXY=${ALL_PROXY} \
    -e NO_PROXY=${NO_PROXY} \
    -v ${CACHE_DIR}:/root/.cache/huggingface \
    -e NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    --name vllm-server \
    vllm/vllm-openai:$VLLM_VERSION \
    --model $MODEL_PATH \
    --served-model-name qwen2.5-7b \
    --max-model-len 8192 \
    --dtype bfloat16 \
    --enforce-eager

echo "启动指令已发出，正在等待 vLLM 就绪（最长 ${READY_TIMEOUT_SECONDS} 秒）..."
START_TS=$(date +%s)
while true; do
    if curl -fsS --max-time 5 "http://127.0.0.1:${HOST_PORT}/v1/models" >/dev/null 2>&1; then
        echo "vLLM 已就绪：http://127.0.0.1:${HOST_PORT}/v1/models"
        break
    fi

    NOW_TS=$(date +%s)
    ELAPSED=$((NOW_TS - START_TS))
    if [ ${ELAPSED} -ge ${READY_TIMEOUT_SECONDS} ]; then
        echo "vLLM 在 ${READY_TIMEOUT_SECONDS} 秒内未就绪。"
        echo "请执行: docker logs --tail 200 vllm-server"
        exit 1
    fi
    sleep 5
done

echo "如需查看加载进度，请执行: docker logs -f vllm-server"