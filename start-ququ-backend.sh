#!/bin/bash
# QuQu Backend 快速启动和测试脚本

set -e

echo "============================================"
echo "  QuQu Backend 启动脚本"
echo "  GPU加速FunASR语音识别服务"
echo "============================================"
echo ""

# 检查必要文件
echo "📋 检查必要文件..."
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 未找到 docker-compose.yml"
    exit 1
fi

if [ ! -d "ququ_backend" ]; then
    echo "❌ 未找到 ququ_backend 目录"
    exit 1
fi

echo "✅ 文件检查通过"
echo ""

# 检查GPU
echo "🎮 检查GPU状态..."
if ! nvidia-smi > /dev/null 2>&1; then
    echo "⚠️ 警告: nvidia-smi不可用，GPU可能无法使用"
else
    echo "✅ GPU可用"
    nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader
fi
echo ""

# 检查Ollama
echo "🤖 检查Ollama服务..."
if curl -s http://localhost:11434/v1/models > /dev/null 2>&1; then
    echo "✅ Ollama服务可用"
    ollama list 2>/dev/null || echo "  模型列表获取失败"
else
    echo "⚠️ 警告: Ollama服务不可用"
    echo "   请确保Ollama正在运行: ollama serve"
fi
echo ""

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose stop ququ-backend 2>/dev/null || true
docker-compose rm -f ququ-backend 2>/dev/null || true
echo ""

# 启动QuQu Backend
echo "🚀 启动QuQu Backend服务..."
docker-compose up -d ququ-backend

echo ""
echo "⏳ 等待服务启动（30秒）..."
sleep 5

# 显示日志
echo ""
echo "📝 服务日志（前20行）:"
echo "----------------------------------------"
docker-compose logs --tail=20 ququ-backend
echo "----------------------------------------"
echo ""

# 等待服务就绪
echo "⏳ 等待API就绪..."
for i in {1..25}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✅ API服务就绪！"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# 测试API
echo ""
echo "🧪 测试API端点..."
echo ""

echo "1️⃣  测试健康检查:"
curl -s http://localhost:8000/api/health | python3 -m json.tool 2>/dev/null || echo "❌ 健康检查失败"
echo ""

echo "2️⃣  测试服务状态:"
curl -s http://localhost:8000/api/status | python3 -m json.tool 2>/dev/null || echo "❌ 状态检查失败"
echo ""

# 显示服务信息
echo "============================================"
echo "  QuQu Backend 已启动！"
echo "============================================"
echo ""
echo "📡 API地址:"
echo "   http://192.168.100.38:8000"
echo "   http://localhost:8000"
echo ""
echo "📚 API文档:"
echo "   http://192.168.100.38:8000/docs"
echo "   http://localhost:8000/docs"
echo ""
echo "🔍 查看日志:"
echo "   docker-compose logs -f ququ-backend"
echo ""
echo "🛑 停止服务:"
echo "   docker-compose stop ququ-backend"
echo ""
echo "🧪 测试语音识别（需要音频文件）:"
echo "   curl -X POST http://localhost:8000/api/asr/transcribe \\"
echo "     -F 'audio=@test.wav'"
echo ""
echo "🧪 测试文本优化:"
echo "   curl -X POST http://localhost:8000/api/llm/optimize \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"text\": \"这个嗯那个就是说我们今天要开会\", \"mode\": \"optimize\"}'"
echo ""
echo "============================================"
