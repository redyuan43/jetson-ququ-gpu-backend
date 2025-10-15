#!/bin/bash

# Jetson AGX Orin DeepResearch 快速诊断脚本
# 用法: ./diagnose.sh

echo "🔍 Jetson DeepResearch 环境诊断 $(date)"
echo "=================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo ""
echo "📊 系统信息:"
echo "-------------"
echo "系统: $(uname -a)"
echo "时间: $(date)"
echo "运行时间: $(uptime -p)"

# 检查内存
echo ""
echo "💾 内存状态:"
echo "-------------"
MEMORY_GB=$(free -g | awk 'NR==2{printf "%.0f", $2}')
if [ $MEMORY_GB -ge 64 ]; then
    check_pass "物理内存: ${MEMORY_GB}GB (充足)"
elif [ $MEMORY_GB -ge 32 ]; then
    check_warn "物理内存: ${MEMORY_GB}GB (可用，但推荐64GB)"
else
    check_fail "物理内存: ${MEMORY_GB}GB (不足，需要至少32GB)"
fi

# 检查磁盘空间
echo ""
echo "💽 磁盘空间:"
echo "-------------"
DISK_AVAIL=$(df -h /data | awk 'NR==2 {print $4}')
DISK_AVAIL_GB=$(df -BG /data | awk 'NR==2 {print $4}' | sed 's/G//')
if [ $DISK_AVAIL_GB -ge 50 ]; then
    check_pass "可用磁盘: ${DISK_AVAIL} (充足)"
elif [ $DISK_AVAIL_GB -ge 20 ]; then
    check_warn "可用磁盘: ${DISK_AVAIL} (可用，但推荐50GB+)"
else
    check_fail "可用磁盘: ${DISK_AVAIL} (不足，需要至少20GB)"
fi

# 检查GPU和CUDA
echo ""
echo "🎮 GPU/CUDA状态:"
echo "-----------------"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | while IFS=',' read -r name driver memory; do
        echo "GPU: $name"
        echo "驱动: $driver"
        echo "显存: $memory"
    done
    check_pass "NVIDIA驱动正常工作"
else
    check_fail "nvidia-smi不可用，请检查NVIDIA驱动"
fi

# 检查CUDA版本
if [ -f /usr/local/cuda/version.txt ]; then
    CUDA_VERSION=$(cat /usr/local/cuda/version.txt | sed 's/.* //')
    check_pass "CUDA版本: $CUDA_VERSION"
elif [ -f /usr/local/cuda/version.json ]; then
    CUDA_VERSION=$(cat /usr/local/cuda/version.json | grep -o '"version" : "[^"]*' | cut -d'"' -f4)
    check_pass "CUDA版本: $CUDA_VERSION"
else
    check_warn "CUDA版本信息未找到"
fi

# 检查Docker
echo ""
echo "🐳 Docker状态:"
echo "-------------"
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        check_pass "Docker服务运行正常"

        # 检查NVIDIA runtime
        if docker info 2>/dev/null | grep -q nvidia; then
            check_pass "NVIDIA runtime可用"
        else
            check_fail "NVIDIA runtime未配置"
        fi
    else
        check_fail "Docker服务未运行"
    fi
else
    check_fail "Docker未安装"
fi

# 检查容器状态
echo ""
echo "📦 容器状态:"
echo "-------------"
if docker-compose ps 2>/dev/null | grep -q "Up"; then
    check_pass "DeepResearch容器运行中"
    docker-compose ps
elif docker-compose ps 2>/dev/null | grep -q "Exit"; then
    check_fail "DeepResearch容器已停止"
    docker-compose ps
else
    check_warn "DeepResearch容器未启动"
fi

# 检查模型文件
echo ""
echo "🧠 模型文件:"
echo "-------------"
MODEL_PATH="/data/sensor-voice/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf"
if [ -f "$MODEL_PATH" ]; then
    MODEL_SIZE=$(ls -lh $MODEL_PATH | awk '{print $5}')
    check_pass "模型文件存在: $MODEL_SIZE"
else
    check_fail "模型文件不存在: $MODEL_PATH"
fi

# 检查llama.cpp
echo ""
echo "⚙️  llama.cpp状态:"
echo "------------------"
LLAMA_CLI="/data/sensor-voice/sensor-voice/llama.cpp/build/bin/llama-cli"
if [ -f "$LLAMA_CLI" ]; then
    export LD_LIBRARY_PATH=/data/sensor-voice/sensor-voice/llama.cpp/build/bin:$LD_LIBRARY_PATH
    if $LLAMA_CLI --version &>/dev/null; then
        check_pass "llama-cli工作正常"
    else
        check_fail "llama-cli无法运行（库文件问题）"
    fi
else
    check_fail "llama-cli未找到"
fi

# 检查HuggingFace登录
echo ""
echo "🤗 HuggingFace状态:"
echo "-------------------"
if command -v huggingface-cli &> /dev/null; then
    if huggingface-cli whoami &>/dev/null; then
        USERNAME=$(huggingface-cli whoami 2>/dev/null | head -1)
        check_pass "HuggingFace已登录: $USERNAME"
    else
        check_fail "HuggingFace未登录"
    fi
else
    check_fail "huggingface-cli未安装"
fi

# 检查PyTorch CUDA（如果在容器中）
if docker-compose ps 2>/dev/null | grep -q "Up"; then
    echo ""
    echo "🔥 PyTorch CUDA测试:"
    echo "--------------------"
    if docker-compose exec -T jetson-deepresearch python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null | grep -q "True"; then
        check_pass "容器内PyTorch CUDA可用"
    else
        check_fail "容器内PyTorch CUDA不可用"
    fi
fi

# 性能测试建议
echo ""
echo "💡 性能建议:"
echo "-------------"
if [ $MEMORY_GB -ge 64 ]; then
    echo "• 建议GPU层数: --n-gpu-layers 35"
    echo "• 建议上下文: --ctx-size 8192"
elif [ $MEMORY_GB -ge 32 ]; then
    echo "• 建议GPU层数: --n-gpu-layers 20"
    echo "• 建议上下文: --ctx-size 4096"
else
    echo "• 建议GPU层数: --n-gpu-layers 10"
    echo "• 建议上下文: --ctx-size 2048"
fi

# 快速修复建议
echo ""
echo "🔧 快速修复:"
echo "-------------"
echo "• 重新登录HuggingFace: huggingface-cli login"
echo "• 启动容器: docker-compose up -d"
echo "• 查看日志: docker-compose logs -f"
echo "• 测试模型: ./test_deepresearch.sh"
echo ""
echo "=================================="
echo "诊断完成！如有❌项目，请先解决再继续。"
echo "时间: $(date)"