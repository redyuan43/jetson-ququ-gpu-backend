#!/bin/bash

echo "🚀 启动 Jetson DeepResearch 环境..."

# 检查 docker-compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose 未安装，请先安装"
    exit 1
fi

# 检查模型文件
if [ ! -f "/data/sensor-voice/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf" ]; then
    echo "⚠️  模型文件不存在，请先下载:"
    echo "   huggingface-cli download bartowski/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-GGUF Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf --local-dir /data/sensor-voice/models"
    exit 1
fi

# 启动容器
echo "📦 启动容器..."
docker-compose up -d jetson-deepresearch

# 等待容器启动
echo "⏳ 等待容器启动..."
sleep 10

# 检查容器状态
if docker-compose ps | grep -q "Up"; then
    echo "✅ 容器启动成功！"
    echo ""
    echo "🔧 常用命令:"
    echo "   进入容器: docker-compose exec jetson-deepresearch bash"
    echo "   查看日志: docker-compose logs -f jetson-deepresearch"
    echo "   停止容器: docker-compose down"
    echo ""
    echo "🧪 测试 llama.cpp:"
    echo "   export LD_LIBRARY_PATH=/workspace/llama.cpp/build/bin:\$LD_LIBRARY_PATH"
    echo "   /workspace/llama.cpp/build/bin/llama-cli --model /workspace/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf --help"
else
    echo "❌ 容器启动失败，请检查日志:"
    docker-compose logs jetson-deepresearch
    exit 1
fi