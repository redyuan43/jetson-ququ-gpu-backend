# QuQu Backend 开机自启配置文档

## ✅ 配置状态

QuQu Backend已完整配置开机自启，无需手动操作。

## 🔄 自动启动流程

```
设备开机
  ↓
Docker服务自动启动 (systemd)
  ↓
ququ-backend容器自动启动 (restart: unless-stopped)
  ↓
FunASR模型自动加载 (~17秒)
  ↓
API服务自动就绪 ✅
```

## 📋 配置详情

### 1. Docker服务

```bash
# 查看Docker开机自启状态
systemctl is-enabled docker
# 输出: enabled ✅
```

### 2. 容器重启策略

```yaml
# docker-compose.yml
services:
  ququ-backend:
    restart: unless-stopped  # ✅ 自动重启策略
```

**`unless-stopped` 策略说明：**
- 容器退出时自动重启
- 手动停止后不会自动重启
- Docker服务启动时自动启动容器
- **推荐用于生产环境**

### 3. 模型缓存持久化

```yaml
volumes:
  # FunASR模型缓存（2.0GB）
  - /data/deepresearch/modelscope_cache:/root/.cache/modelscope
```

**好处：**
- 避免每次启动重新下载模型
- 初始化时间：~17秒（从缓存加载）
- 节省带宽和时间

## 🔍 状态检查

### 快速检查脚本

```bash
# 运行状态检查脚本
./check-autostart.sh
```

### 手动检查命令

```bash
# 1. 检查Docker服务
systemctl status docker

# 2. 检查容器状态
docker ps --filter name=ququ-backend

# 3. 检查API服务
curl http://localhost:8000/api/health

# 4. 检查详细状态
curl http://localhost:8000/api/status | python3 -m json.tool
```

## ⏱️ 启动时间

| 阶段 | 时间 | 说明 |
|------|------|------|
| 设备开机 | ~30秒 | 系统启动 |
| Docker启动 | ~5秒 | Docker服务就绪 |
| 容器启动 | ~2秒 | 容器创建完成 |
| 模型加载 | ~17秒 | FunASR模型初始化 |
| **总计** | **~54秒** | **从开机到服务就绪** |

## 🛠️ 常见操作

### 查看服务日志

```bash
# 实时查看日志
docker-compose logs -f ququ-backend

# 查看最近50行日志
docker-compose logs --tail=50 ququ-backend
```

### 手动重启服务

```bash
# 重启容器
docker-compose restart ququ-backend

# 完全重建容器（不推荐，会触发模型重新加载）
docker-compose down ququ-backend
docker-compose up -d ququ-backend
```

### 临时停止服务

```bash
# 停止容器（不会自动启动，除非重启Docker）
docker-compose stop ququ-backend

# 启动容器
docker-compose start ququ-backend
```

### 禁用开机自启

如果需要禁用开机自启：

```bash
# 修改docker-compose.yml中的restart策略
# 将 restart: unless-stopped 改为 restart: "no"

# 或者手动停止容器
docker stop ququ-backend
```

## 🔧 故障排查

### 问题1: 开机后服务未启动

```bash
# 1. 检查Docker服务
systemctl status docker

# 2. 检查容器是否存在
docker ps -a --filter name=ququ-backend

# 3. 手动启动容器
docker start ququ-backend

# 4. 查看启动日志
docker logs ququ-backend
```

### 问题2: 服务启动但API不可用

```bash
# 1. 等待模型加载完成（约17秒）
sleep 20

# 2. 检查服务日志
docker-compose logs --tail=30 ququ-backend | grep -E "(初始化|✅|❌)"

# 3. 检查FunASR模型
docker exec ququ-backend ls -lh /root/.cache/modelscope/hub/damo/
```

### 问题3: 模型加载过慢

```bash
# 检查模型缓存是否正确映射
docker exec ququ-backend bash -c "du -sh /root/.cache/modelscope && ls -la /root/.cache/modelscope/hub/damo/"

# 应该显示约2.0GB的缓存
```

## 📊 监控建议

### 服务健康检查

容器配置了自动健康检查：

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
  interval: 30s      # 每30秒检查一次
  timeout: 10s       # 10秒超时
  retries: 3         # 失败3次标记为unhealthy
  start_period: 120s # 启动后120秒内不检查
```

### 查看健康状态

```bash
# 查看容器健康状态
docker inspect ququ-backend --format='{{.State.Health.Status}}'
# 输出: healthy / unhealthy / starting
```

## 🎯 最佳实践

1. **定期检查日志**
   ```bash
   docker-compose logs --tail=100 ququ-backend
   ```

2. **监控GPU使用率**
   ```bash
   nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv -l 1
   ```

3. **备份配置文件**
   ```bash
   cp docker-compose.yml docker-compose.yml.backup
   cp -r ququ_backend ququ_backend.backup
   ```

4. **定期清理日志**
   ```bash
   docker-compose logs --tail=0 ququ-backend  # 清空日志
   ```

## 📞 支持信息

- **API文档**: http://192.168.100.38:8000/docs
- **健康检查**: http://192.168.100.38:8000/api/health
- **服务状态**: http://192.168.100.38:8000/api/status

## 📝 相关文档

- [DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md) - 完整部署文档
- [CLAUDE.md](./CLAUDE.md) - Claude Code项目指南
- [ququ_backend/README.md](./ququ_backend/README.md) - 后端API文档
- [start-ququ-backend.sh](./start-ququ-backend.sh) - 启动测试脚本
- [check-autostart.sh](./check-autostart.sh) - 状态检查脚本

---

**配置完成时间**: 2025-10-15
**最后更新**: 2025-10-15
**状态**: ✅ 生产就绪
