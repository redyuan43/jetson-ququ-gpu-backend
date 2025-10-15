# 🚀 Jetson DeepResearch 快速启动

## 1分钟上手

### 1. 启动环境
```bash
# 一键启动基础环境
./start.sh

# 进入容器
docker-compose exec jetson-deepresearch bash
```

### 2. 测试模型
```bash
# 在容器内运行测试
./test_deepresearch.sh
```

### 3. 启动API服务器
```bash
# 一键启动服务器
./start-server.sh

# 测试API
curl http://localhost:8080/v1/models
```

## 🎯 常用命令

### 容器管理
```bash
# 启动
docker-compose up -d

# 停止
docker-compose down

# 重启
docker-compose restart

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 模型测试
```bash
# 设置环境变量
export LD_LIBRARY_PATH=/workspace/llama.cpp/build/bin:$LD_LIBRARY_PATH

# 简单测试
/workspace/llama.cpp/build/bin/llama-cli \
  --model /workspace/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf \
  --ctx-size 1024 \
  --n-gpu-layers 35 \
  --threads 8 \
  --predict 50 \
  --prompt "你好" \
  --temp 0.7
```

### API调用
```bash
# 获取模型列表
curl http://localhost:8080/v1/models

# 文本生成
curl -X POST http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf",
    "prompt": "请介绍一下人工智能",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

## 📁 文件结构

```
/data/deepresearch/
├── docker-compose.yml          # Docker Compose配置
├── start.sh                    # 一键启动脚本
├── start-server.sh            # 启动API服务器
├── test_deepresearch.sh       # 环境测试脚本
├── README_DOCKER.md           # 详细文档
└── QUICK_START.md             # 快速指南

/data/sensor-voice/
├── models/
│   └── Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf  # 18GB模型
├── llama.cpp/                 # 已编译的llama.cpp
└── DeepResearch/              # 项目代码
```

## ⚡ 性能指标

- **模型大小**: 18GB (Q4_K_M量化)
- **内存占用**: 20-25GB
- **推理速度**: 3-5 tokens/秒
- **上下文长度**: 最大8192 tokens
- **GPU层数**: 35层 (推荐)

## 🔧 故障排查

### 容器无法启动
```bash
# 检查Docker状态
sudo systemctl status docker

# 检查NVIDIA runtime
docker info | grep -i nvidia
```

### GPU不可用
```bash
# 在容器内检查
python3 -c "import torch; print('CUDA:', torch.cuda.is_available())"

# 检查GPU状态
nvidia-smi
```

### 模型加载失败
```bash
# 检查模型文件
ls -lh /data/sensor-voice/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf

# 检查llama.cpp
ls -la /data/sensor-voice/sensor-voice/llama.cpp/build/bin/
```

## 🚀 下一步

1. **运行DeepResearch项目**:
   ```bash
   cd /data/sensor-voice/DeepResearch
   python inference/run_multi_react.py --help
   ```

2. **集成到应用**: 使用API接口集成到你的应用中

3. **性能优化**: 调整GPU层数和批处理大小

## 📞 支持

有问题？检查这些：
- 查看日志: `docker-compose logs`
- 验证GPU: `nvidia-smi`
- 测试环境: `./test_deepresearch.sh`
- 文档: `README_DOCKER.md`