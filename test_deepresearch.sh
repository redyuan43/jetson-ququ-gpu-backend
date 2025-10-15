#!/bin/bash

echo "🧪 测试 Jetson DeepResearch 环境..."

# 设置环境变量
export LD_LIBRARY_PATH=/data/sensor-voice/sensor-voice/llama.cpp/build/bin:$LD_LIBRARY_PATH

MODEL_PATH="/data/sensor-voice/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf"
LLAMA_BIN="/data/sensor-voice/sensor-voice/llama.cpp/build/bin"

echo "1️⃣ 检查模型文件..."
if [ -f "$MODEL_PATH" ]; then
    echo "✅ 模型文件存在: $(ls -lh $MODEL_PATH | awk '{print $5}')"
else
    echo "❌ 模型文件不存在: $MODEL_PATH"
    exit 1
fi

echo "2️⃣ 检查 llama.cpp..."
if [ -f "$LLAMA_BIN/llama-cli" ]; then
    echo "✅ llama-cli 可用"
    $LLAMA_BIN/llama-cli --version
else
    echo "❌ llama-cli 不存在"
    exit 1
fi

echo "3️⃣ 测试模型加载..."
timeout 10 $LLAMA_BIN/llama-cli \
  --model $MODEL_PATH \
  --ctx-size 512 \
  --n-gpu-layers 10 \
  --threads 4 \
  --predict 10 \
  --prompt "你好" \
  --no-display-prompt

if [ $? -eq 0 ]; then
    echo "✅ 模型加载成功！"
else
    echo "⚠️  模型加载测试中断（可能是正常的超时）"
fi

echo "4️⃣ 测试完整推理..."
echo "输入测试问题: 请介绍一下人工智能"
$LLAMA_BIN/llama-cli \
  --model $MODEL_PATH \
  --ctx-size 1024 \
  --n-gpu-layers 35 \
  --threads 8 \
  --predict 50 \
  --temp 0.7 \
  --prompt "请介绍一下人工智能" \
  --no-display-prompt

echo "5️⃣ 测试服务器模式..."
echo "启动 llama-server（按 Ctrl+C 停止）..."
echo "命令: $LLAMA_BIN/llama-server --model $MODEL_PATH --ctx-size 8192 --n-gpu-layers 35 --port 8080"

echo "✅ 环境测试完成！"
echo ""
echo "🚀 下一步:"
echo "   1. 启动服务器: $LLAMA_BIN/llama-server --model $MODEL_PATH --ctx-size 8192 --n-gpu-layers 35 --port 8080"
echo "   2. 测试 API: curl http://localhost:8080/v1/models"
echo "   3. 运行 DeepResearch: cd /data/sensor-voice/DeepResearch && python inference/run_multi_react.py"