#!/bin/bash
# QuQu Backend 热词功能测试脚本

set -e

echo "============================================"
echo "  QuQu Backend 热词功能测试"
echo "============================================"
echo ""

BACKEND_URL="http://localhost:8000"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. 测试健康检查
echo "1️⃣  测试后端健康状态..."
if curl -sf "$BACKEND_URL/api/health" > /dev/null; then
    echo -e "${GREEN}✅ 后端服务正常${NC}"
else
    echo -e "${RED}❌ 后端服务不可用${NC}"
    exit 1
fi
echo ""

# 2. 测试热词API
echo "2️⃣  测试热词API..."
HOTWORDS_RESPONSE=$(curl -s "$BACKEND_URL/api/hotwords")

if echo "$HOTWORDS_RESPONSE" | grep -q '"success": true'; then
    HOTWORDS_COUNT=$(echo "$HOTWORDS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['count'])")
    echo -e "${GREEN}✅ 热词API正常${NC}"
    echo "   已加载热词数量: $HOTWORDS_COUNT"
else
    echo -e "${RED}❌ 热词API异常${NC}"
    exit 1
fi
echo ""

# 3. 查看热词列表（前10个）
echo "3️⃣  热词列表预览（前10个）:"
echo "$HOTWORDS_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for i, word in enumerate(data['hotwords'][:10], 1):
    print(f'   {i}. {word}')
"
echo "   ..."
echo ""

# 4. 验证关键热词是否存在
echo "4️⃣  验证关键AI术语是否在热词表中:"

KEYWORDS=("Gemma" "千问" "GPT" "Claude" "LLaMA" "Ollama" "PyTorch" "CUDA" "Jetson" "大模型")

for keyword in "${KEYWORDS[@]}"; do
    if echo "$HOTWORDS_RESPONSE" | grep -q "\"$keyword\""; then
        echo -e "   ${GREEN}✅${NC} $keyword - 已加载"
    else
        echo -e "   ${YELLOW}⚠️${NC}  $keyword - 未找到"
    fi
done
echo ""

# 5. 测试热词重新加载
echo "5️⃣  测试热词重新加载功能..."
RELOAD_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/hotwords/reload")

if echo "$RELOAD_RESPONSE" | grep -q '"success": true'; then
    RELOAD_COUNT=$(echo "$RELOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['count'])")
    echo -e "${GREEN}✅ 热词重新加载成功${NC}"
    echo "   重新加载后热词数量: $RELOAD_COUNT"
else
    echo -e "${RED}❌ 热词重新加载失败${NC}"
    exit 1
fi
echo ""

# 6. 查看后端服务状态
echo "6️⃣  查看后端服务详细状态..."
STATUS_RESPONSE=$(curl -s "$BACKEND_URL/api/status")

echo "$STATUS_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'   FunASR状态: {\"✅ 已初始化\" if data[\"funasr\"][\"initialized\"] else \"❌ 未初始化\"}')
print(f'   Ollama状态: {\"✅ 可用\" if data[\"ollama\"][\"available\"] else \"❌ 不可用\"}')
print(f'   GPU状态: {\"✅ 可用\" if data[\"gpu_available\"] else \"❌ 不可用\"}')
" 2>/dev/null || echo "   状态信息解析失败"
echo ""

# 总结
echo "============================================"
echo "  测试总结"
echo "============================================"
echo -e "${GREEN}✅ 所有热词功能测试通过！${NC}"
echo ""
echo "📝 使用提示："
echo "  1. 热词文件位置: /data/deepresearch/ququ_backend/hotwords.txt"
echo "  2. 编辑热词后会自动重新加载"
echo "  3. 也可手动触发重新加载："
echo "     curl -X POST $BACKEND_URL/api/hotwords/reload"
echo ""
echo "🎯 热词功能已启用，将提升以下术语的识别准确率："
echo "  - AI模型名称（Gemma, 千问, GPT, Claude等）"
echo "  - 技术术语（大模型, LLM, 微调, 量化等）"
echo "  - 框架工具（PyTorch, TensorFlow, Ollama等）"
echo "  - 硬件相关（GPU, CUDA, Jetson等）"
echo ""
echo "============================================"
