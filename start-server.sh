#!/bin/bash

echo "🚀 启动 llama.cpp 服务器..."

# 检查容器是否已启动
if ! docker-compose ps | grep -q "jetson-deepresearch.*Up"; then
    echo "⚠️  主容器未启动，先启动主容器..."
    ./start.sh
fi

# 启动 llama.cpp 服务器
echo "🔧 启动 llama.cpp 服务器..."
docker-compose --profile server up -d llama-server

# 等待服务器启动
echo "⏳ 等待服务器启动..."
sleep 15

# 检查服务器状态
if docker-compose ps | grep -q "llama-server.*Up"; then
    echo "✅ llama.cpp 服务器启动成功！"
    echo ""
    echo "🌐 API 端点:"
    echo "   - 模型列表: http://localhost:8080/v1/models"
    echo "   - 健康检查: http://localhost:8080/health"
    echo "   - OpenAI 兼容 API: http://localhost:8080/v1/completions"
    echo ""
    echo "🧪 测试 API:"
    echo "   curl http://localhost:8080/v1/models"
    echo ""
    echo "📊 查看日志:"
    echo "   docker-compose logs -f llama-server"
else
    echo "❌ 服务器启动失败，请检查日志:"
    docker-compose logs llama-server
    exit 1
fi

# 测试 API
echo "🧪 测试 API 连接..."
sleep 5
if curl -s http://localhost:8080/health > /dev/null; then
    echo "✅ API 连接正常！"
else
    echo "⚠️  API 可能还在启动中，请稍后再试"
fi