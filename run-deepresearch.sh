#!/bin/bash

# Jetson DeepResearch 一键运行脚本
# 包含所有复杂的环境配置和运行指令

set -e  # 遇到错误时退出

echo "🚀 Jetson DeepResearch 一键运行脚本"
echo "=================================="

# 添加Docker Compose到PATH
export PATH=$PATH:~/.local/bin

# 检查Docker Compose
echo "📦 检查Docker Compose..."
if ! command -v docker-compose > /dev/null; then
    echo "❌ Docker Compose未安装，请先安装"
    exit 1
fi

echo "✅ Docker Compose已安装: $(docker-compose --version)"

# 检查模型文件
echo "🧠 检查模型文件..."
MODEL_PATH="/data/sensor-voice/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf"
if [ ! -f "$MODEL_PATH" ]; then
    echo "❌ 模型文件不存在: $MODEL_PATH"
    echo "请先下载模型:"
    echo "  huggingface-cli download bartowski/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-GGUF Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf --local-dir /data/sensor-voice/models"
    exit 1
fi

echo "✅ 模型文件存在: $(ls -lh $MODEL_PATH | awk '{print $5}')"

# 检查llama.cpp
echo "⚙️  检查llama.cpp..."
LLAMA_PATH="/data/sensor-voice/sensor-voice/llama.cpp/build/bin/llama-cli"
if [ ! -f "$LLAMA_PATH" ]; then
    echo "❌ llama.cpp未编译，请先编译:"
    echo "  cd /data/sensor-voice/sensor-voice/llama.cpp && make -j8 LLAMA_CUDA=1"
    exit 1
fi

echo "✅ llama.cpp可用"

# 检查DeepResearch项目
echo "📁 检查DeepResearch项目..."
DEEPRESEARCH_PATH="/data/deepresearch/DeepResearch"
if [ ! -d "$DEEPRESEARCH_PATH" ]; then
    echo "❌ DeepResearch项目不存在: $DEEPRESEARCH_PATH"
    exit 1
fi

echo "✅ DeepResearch项目存在"

# 创建输出目录
mkdir -p /data/deepresearch/outputs

# 停止现有容器
echo "🛑 停止现有容器..."
docker-compose down 2>/dev/null || true

# 清理旧容器
echo "🧹 清理旧容器..."
docker container prune -f >/dev/null 2>&1 || true

# 启动基础环境
echo "🔥 启动DeepResearch基础环境..."
docker-compose up -d jetson-deepresearch

echo "⏳ 等待容器启动..."
sleep 10

# 检查容器状态
echo "🔍 检查容器状态..."
if docker-compose ps | grep -q "Up.*jetson-deepresearch"; then
    echo "✅ 基础容器启动成功"
else
    echo "❌ 基础容器启动失败"
    docker-compose logs jetson-deepresearch
    exit 1
fi

# 测试环境
echo "🧪 测试环境..."
docker-compose exec -T jetson-deepresearch bash -c "
    echo 'Testing PyTorch CUDA...' &&
    python3 -c 'import torch; print(f\"PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}\")' &&
    echo 'Testing llama.cpp...' &&
    export LD_LIBRARY_PATH=/workspace/llama.cpp/build/bin:\$LD_LIBRARY_PATH &&
    /workspace/llama.cpp/build/bin/llama-cli --version
"

echo ""
echo "🎯 运行选项:"
echo "1. 运行基础测试 (推荐)"
echo "2. 运行llama.cpp服务器"
echo "3. 运行DeepResearch推理"
echo "4. 进入交互模式"
echo ""

read -p "请选择运行模式 (1-4): " choice

case $choice in
    1)
        echo "🧪 运行基础测试..."
        docker-compose exec jetson-deepresearch bash -c "
            export LD_LIBRARY_PATH=/workspace/llama.cpp/build/bin:\$LD_LIBRARY_PATH &&
            echo 'Testing model loading...' &&
            /workspace/llama.cpp/build/bin/llama-cli \
                --model /workspace/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf \
                --ctx-size 512 \
                --n-gpu-layers 35 \
                --threads 8 \
                --predict 20 \
                --prompt '你好，请介绍一下阿里巴巴的WebAgent技术' \
                --temp 0.7 \
                --no-display-prompt
        "
        ;;

    2)
        echo "🌐 启动llama.cpp服务器..."
        docker-compose --profile server up -d llama-server
        echo "✅ llama.cpp服务器已启动"
        echo "📡 API地址: http://localhost:8080"
        echo "📊 查看日志: docker-compose logs -f llama-server"
        ;;

    3)
        echo "🧠 运行DeepResearch推理..."
        docker-compose --profile inference up deepresearch-runner
        echo "✅ DeepResearch推理完成"
        echo "📊 查看输出: ls -la /data/deepresearch/outputs/"
        ;;

    4)
        echo "🔧 进入交互模式..."
        echo "可用的命令:"
        echo "  export LD_LIBRARY_PATH=/workspace/llama.cpp/build/bin:\$LD_LIBRARY_PATH"
        echo "  /workspace/llama.cpp/build/bin/llama-cli --model /workspace/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf --help"
        echo "  python3 /workspace/DeepResearch/inference/run_multi_react.py --help"
        echo ""
        echo "正在进入容器..."
        docker-compose exec jetson-deepresearch bash
        ;;

    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "🎉 运行完成！"
echo "📊 查看容器状态: docker-compose ps"
echo "📋 查看日志: docker-compose logs -f"
echo "🧪 更多测试: ./test_deepresearch.sh"
echo "🔍 环境诊断: ./diagnose.sh"
echo ""
echo "💡 提示:"
echo "  - 模型文件: /workspace/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf"
echo "  - llama.cpp: /workspace/llama.cpp/build/bin/llama-cli"
echo "  - DeepResearch: /workspace/DeepResearch/"
echo "  - 输出目录: /data/deepresearch/outputs/"