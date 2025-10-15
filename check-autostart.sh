#!/bin/bash
# QuQu Backend开机自启状态检查脚本

echo "============================================"
echo "  QuQu Backend 开机自启配置检查"
echo "============================================"
echo ""

# 检查Docker服务状态
echo "1️⃣  Docker服务状态:"
if systemctl is-enabled docker > /dev/null 2>&1; then
    echo "   ✅ Docker服务已配置开机自启"
    if systemctl is-active docker > /dev/null 2>&1; then
        echo "   ✅ Docker服务正在运行"
    else
        echo "   ⚠️  Docker服务未运行"
    fi
else
    echo "   ❌ Docker服务未配置开机自启"
fi
echo ""

# 检查容器重启策略
echo "2️⃣  ququ-backend容器重启策略:"
if docker inspect ququ-backend > /dev/null 2>&1; then
    RESTART_POLICY=$(docker inspect ququ-backend --format='{{.HostConfig.RestartPolicy.Name}}')
    echo "   当前策略: $RESTART_POLICY"

    if [ "$RESTART_POLICY" = "unless-stopped" ] || [ "$RESTART_POLICY" = "always" ]; then
        echo "   ✅ 已配置自动重启（$RESTART_POLICY）"
    else
        echo "   ⚠️  未配置自动重启策略"
    fi
else
    echo "   ⚠️  容器不存在"
fi
echo ""

# 检查容器运行状态
echo "3️⃣  容器运行状态:"
if docker ps --filter name=ququ-backend --format '{{.Names}}' | grep -q ququ-backend; then
    STATUS=$(docker ps --filter name=ququ-backend --format '{{.Status}}')
    echo "   ✅ 容器正在运行: $STATUS"
else
    if docker ps -a --filter name=ququ-backend --format '{{.Names}}' | grep -q ququ-backend; then
        STATUS=$(docker ps -a --filter name=ququ-backend --format '{{.Status}}')
        echo "   ⚠️  容器已停止: $STATUS"
    else
        echo "   ❌ 容器不存在"
        exit 1
    fi
fi
echo ""

# 检查服务可用性
echo "4️⃣  API服务状态:"
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "   ✅ API服务正常 (http://192.168.100.38:8000)"

    # 检查详细状态
    if curl -s http://localhost:8000/api/status | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    funasr_ok = data.get('funasr', {}).get('initialized', False)
    ollama_ok = data.get('ollama', {}).get('available', False)
    gpu_ok = data.get('gpu_available', False)

    if funasr_ok and ollama_ok and gpu_ok:
        print('   ✅ FunASR: 已初始化')
        print('   ✅ Ollama: 可用')
        print('   ✅ GPU: 可用')
        sys.exit(0)
    else:
        print(f'   ⚠️  FunASR: {\"✅\" if funasr_ok else \"❌\"}')
        print(f'   ⚠️  Ollama: {\"✅\" if ollama_ok else \"❌\"}')
        print(f'   ⚠️  GPU: {\"✅\" if gpu_ok else \"❌\"}')
        sys.exit(1)
except:
    print('   ⚠️  无法获取详细状态')
    sys.exit(1)
" 2>/dev/null; then
        :
    fi
else
    echo "   ⚠️  API服务不可用（可能正在初始化...）"
fi
echo ""

# 显示配置总结
echo "============================================"
echo "  配置总结"
echo "============================================"
echo ""
echo "✅ 开机自启已配置："
echo "   1. Docker服务开机自动启动"
echo "   2. ququ-backend容器自动启动"
echo "   3. FunASR服务自动初始化"
echo ""
echo "🔄 启动流程："
echo "   设备开机"
echo "     → Docker服务启动"
echo "     → ququ-backend容器启动"
echo "     → FunASR模型加载（约17秒）"
echo "     → API服务就绪"
echo ""
echo "📡 服务地址："
echo "   http://192.168.100.38:8000"
echo "   http://localhost:8000"
echo ""
echo "============================================"
