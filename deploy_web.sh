#!/bin/bash

# DeepResearch Web界面部署脚本
# 用于远程访问Web GUI

echo "🌐 部署DeepResearch Web界面..."

# 停止现有容器
echo "🛑 停止现有容器..."
docker-compose down 2>/dev/null || true

# 启动模型服务器
echo "🚀 启动模型服务器..."
docker run -d --name deepresearch-web \
  --runtime nvidia \
  --ipc host \
  --privileged \
  --network host \
  -v /data/deepresearch:/workspace \
  -v /data/sensor-voice/models:/workspace/models \
  -v /data/sensor-voice/sensor-voice/llama.cpp:/workspace/llama.cpp \
  -e NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -e CUDA_VISIBLE_DEVICES=0 \
  -e TORCH_CUDA_ARCH_LIST=8.7 \
  -e PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128 \
  -e LLAMA_CUDA=1 \
  -e GGML_CUDA=1 \
  -e LD_LIBRARY_PATH=/workspace/llama.cpp/build/bin:$LD_LIBRARY_PATH \
  jetson_minicpm_v:latest bash -c "
    # 启动模型服务器
    export LD_LIBRARY_PATH=/workspace/llama.cpp/build/bin:\$LD_LIBRARY_PATH &&
    /workspace/llama.cpp/build/bin/llama-server \
      --model /workspace/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf \
      --ctx-size 8192 \
      --n-gpu-layers 48 \
      --port 8004 \
      --host 0.0.0.0 > /tmp/server.log 2>&1 &

    # 等待模型服务器启动
    sleep 15

    # 启动Web界面
    cd /workspace/DeepResearch/WebAgent/WebDancer
    export GOOGLE_SEARCH_KEY=''
    export JINA_API_KEY=''
    export DASHSCOPE_API_KEY=''

    python3 -m demos.assistant_qwq_chat \
      --server_name=0.0.0.0 \
      --server_port=7860 \
      --share=True
  "

echo "✅ Web界面部署完成！"
echo "📡 访问地址: http://YOUR_SERVER_IP:7860"
echo "🔍 查看日志: docker logs deepresearch-web"
echo "🛑 停止服务: docker stop deepresearch-web && docker rm deepresearch-web"