# Jetson AGX Orin DeepResearch Docker 部署指南

## 🚀 快速开始

使用 docker-compose 管理你的 Jetson DeepResearch 环境：

### 基础命令

```bash
# 启动主容器
docker-compose up -d jetson-deepresearch

# 进入容器
docker-compose exec jetson-deepresearch bash

# 查看日志
docker-compose logs -f jetson-deepresearch

# 停止容器
docker-compose down

# 重新构建
docker-compose build
```

### 启动 llama.cpp 服务器

```bash
# 启动 llama.cpp 服务器（带 DeepResearch Q4_K_M 模型）
docker-compose --profile server up -d llama-server

# 查看服务器状态
docker-compose logs -f llama-server

# 测试 API
curl http://localhost:8080/v1/models
```

## 📋 环境说明

### 容器配置

- **基础镜像**: `jetson_minicpm_v:latest` (已包含 PyTorch 2.4.0 + CUDA 12.6)
- **GPU支持**: NVIDIA runtime，自动检测 Jetson GPU
- **内存限制**: 64GB (适配 Jetson AGX Orin)
- **CPU限制**: 8核

### 目录映射

| 主机路径 | 容器路径 | 用途 |
|---------|---------|------|
| `/data/sensor-voice` | `/workspace` | 主工作目录 |
| `/data/sensor-voice/models` | `/workspace/models` | 模型存储 |
| `/data/sensor-voice/sensor-voice/llama.cpp` | `/workspace/llama.cpp` | llama.cpp 工具 |

### 环境变量

- `NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics`
- `CUDA_VISIBLE_DEVICES=0`
- `TORCH_CUDA_ARCH_LIST=8.7` (适配 Orin GPU)
- `LLAMA_CUDA=1` (启用 CUDA 支持)

## 🎯 使用示例

### 1. 基础推理测试

进入容器后：

```bash
# 设置环境变量
export LD_LIBRARY_PATH=/workspace/llama.cpp/build/bin:$LD_LIBRARY_PATH

# 测试模型
/workspace/llama.cpp/build/bin/llama-cli \
  --model /workspace/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf \
  --ctx-size 8192 \
  --n-gpu-layers 35 \
  --threads 12 \
  --temp 0.85 \
  --prompt "请介绍阿里巴巴的WebAgent技术"
```

### 2. 运行服务器模式

```bash
# 启动服务器
/workspace/llama.cpp/build/bin/llama-server \
  --model /workspace/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf \
  --ctx-size 8192 \
  --n-gpu-layers 35 \
  --port 8080 \
  --host 0.0.0.0
```

### 3. 运行 DeepResearch 项目

```bash
cd /data/sensor-voice/DeepResearch
# 运行你的测试代码
python inference/run_multi_react.py --help
```

## 🔧 故障排除

### 容器启动失败

```bash
# 检查日志
docker-compose logs jetson-deepresearch

# 重新创建容器
docker-compose down
docker-compose up -d
```

### GPU 不可用

```bash
# 在容器内检查
docker-compose exec jetson-deepresearch bash
python3 -c "import torch; print('CUDA:', torch.cuda.is_available())"

# 检查 NVIDIA runtime
docker info | grep -i nvidia
```

### 内存不足

```bash
# 检查内存使用
docker stats

# 调整内存限制（编辑 docker-compose.yml）
mem_limit: 32g  # 减小到 32GB
```

## 📊 性能预期

- **模型大小**: 18GB (Q4_K_M 量化)
- **推理速度**: 3-5 tokens/秒 (Jetson AGX Orin)
- **内存占用**: 20-25GB (含模型加载)
- **功耗**: 30-45W

## 🔄 更新和维护

```bash
# 更新镜像
docker-compose pull

# 清理无用镜像
docker image prune -a

# 备份模型
cp /data/sensor-voice/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf /backup/
```

## 📞 支持

如果遇到问题：
1. 检查容器日志: `docker-compose logs`
2. 验证GPU状态: `nvidia-smi`
3. 确认模型文件: `ls -lh /data/sensor-voice/models/`

## ⚡ 一键启动脚本

创建 `start.sh`:

```bash
#!/bin/bash
echo "🚀 启动 Jetson DeepResearch 环境..."
docker-compose up -d jetson-deepresearch
echo "✅ 容器已启动，使用 'docker-compose exec jetson-deepresearch bash' 进入"
```

创建 `start-server.sh`:

```bash
#!/bin/bash
echo "🚀 启动 llama.cpp 服务器..."
docker-compose --profile server up -d llama-server
echo "✅ 服务器已启动，API 地址: http://localhost:8080"
```