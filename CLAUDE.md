# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**DeepResearch + QuQu Backend** - Jetson AGX Orin平台的AI推理和语音识别服务集成环境

本项目包含两个主要服务：
1. **DeepResearch**: 阿里巴巴通义DeepResearch多智能体推理系统（基于30B模型）
2. **QuQu Backend**: GPU加速的FunASR语音识别服务 + Ollama文本优化（为QuQu客户端提供API）

## 硬件环境

- **平台**: NVIDIA Jetson AGX Orin 64GB
- **GPU**: Ampere架构, 2048 CUDA核心, Compute Capability 8.7
- **CUDA**: 12.6
- **内存**: 64GB物理内存
- **操作系统**: Ubuntu, Linux 5.15.148-tegra

## 项目结构

```
/data/deepresearch/
├── docker-compose.yml          # Docker Compose配置（所有服务）
├── DeepResearch/               # 通义DeepResearch项目
│   ├── inference/              # 推理脚本
│   ├── WebAgent/               # WebAgent相关
│   └── requirements.txt        # Python依赖
├── ququ/                       # QuQu原始项目（客户端）
│   ├── funasr_server.py       # 原始FunASR服务（CPU版）
│   ├── main.js                # Electron主程序
│   └── src/                   # 前端代码
├── ququ_backend/              # QuQu后端服务（GPU版）
│   ├── server.py              # FastAPI主服务
│   ├── funasr_gpu.py          # GPU加速FunASR
│   ├── llm_client.py          # Ollama客户端
│   ├── requirements.txt       # Python依赖
│   └── README.md              # 后端文档
└── outputs/                   # 输出目录

/data/sensor-voice/
├── models/                    # 模型文件目录
│   └── Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf
└── llama.cpp/                 # llama.cpp工具链
```

## Docker服务架构

### 1. jetson-deepresearch（基础容器）
- **容器名**: deepresearch-runner
- **功能**: 基础环境，保持运行
- **端口**: 使用host网络
- **用途**: 交互式开发和测试

### 2. llama-server（可选）
- **Profile**: server
- **功能**: llama.cpp API服务器
- **端口**: 8080
- **模型**: Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf

### 3. deepresearch-runner（可选）
- **Profile**: inference
- **功能**: DeepResearch推理任务
- **用途**: 批量推理和实验

### 4. ququ-backend（QuQu后端）
- **容器名**: ququ-backend
- **功能**: GPU加速FunASR + Ollama文本优化
- **端口**: 8000
- **API文档**: http://192.168.100.38:8000/docs

## 常用命令

### 启动服务

```bash
# 进入项目目录
cd /data/deepresearch

# 启动QuQu Backend
docker-compose up -d ququ-backend

# 启动所有服务（包括llama-server）
docker-compose --profile server up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f ququ-backend
```

### 进入容器

```bash
# 进入QuQu Backend容器
docker exec -it ququ-backend bash

# 进入DeepResearch容器
docker exec -it deepresearch-runner bash

# 在容器内测试GPU
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

### 测试API

```bash
# 检查QuQu Backend状态
curl http://192.168.100.38:8000/api/status

# 测试健康检查
curl http://192.168.100.38:8000/api/health

# 测试语音识别（需要音频文件）
curl -X POST http://192.168.100.38:8000/api/asr/transcribe \
  -F "audio=@test.wav" \
  -F "use_vad=true" \
  -F "use_punc=true"

# 测试文本优化
curl -X POST http://192.168.100.38:8000/api/llm/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "这个嗯那个就是说我们今天要开会",
    "mode": "optimize"
  }'
```

### DeepResearch相关

```bash
# 进入DeepResearch目录
cd /data/deepresearch/DeepResearch

# 运行推理
python3 inference/run_multi_react.py --help

# 测试llama.cpp
docker exec deepresearch-runner bash -c "
  export LD_LIBRARY_PATH=/workspace/llama.cpp/build/bin:\$LD_LIBRARY_PATH &&
  /workspace/llama.cpp/build/bin/llama-cli \
    --model /workspace/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf \
    --ctx-size 1024 \
    --n-gpu-layers 35 \
    --prompt '你好'
"
```

## 关键配置

### 环境变量

**QuQu Backend容器:**
```bash
CUDA_VISIBLE_DEVICES=0          # GPU设备
OLLAMA_BASE_URL=http://192.168.100.38:11434  # Ollama地址
OLLAMA_MODEL=gpt-oss:20b        # 使用的LLM模型
SERVER_PORT=8000                # API端口
```

**DeepResearch容器:**
```bash
MODEL_PATH=/workspace/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf
CUDA_VISIBLE_DEVICES=0
LLAMA_CUDA=1
```

### GPU配置

所有服务都配置了NVIDIA GPU访问：
- Runtime: nvidia
- Device capabilities: [gpu]
- CUDA_VISIBLE_DEVICES=0

### 网络配置

- **network_mode: host** - 所有服务使用宿主机网络
- QuQu Backend API: http://192.168.100.38:8000
- Ollama (宿主机): http://192.168.100.38:11434
- llama-server (可选): http://192.168.100.38:8080

## 开发流程

### 修改QuQu Backend

1. 编辑代码:
   ```bash
   cd /data/deepresearch/ququ_backend
   vim server.py  # 或其他文件
   ```

2. 重启服务:
   ```bash
   docker-compose restart ququ-backend
   ```

3. 查看日志:
   ```bash
   docker-compose logs -f ququ-backend
   ```

### 修改DeepResearch

1. 编辑代码:
   ```bash
   cd /data/deepresearch/DeepResearch
   vim inference/run_multi_react.py
   ```

2. 在容器内测试:
   ```bash
   docker exec -it deepresearch-runner bash
   cd /workspace/DeepResearch
   python3 inference/run_multi_react.py --help
   ```

## 故障排查

### QuQu Backend无法启动

```bash
# 检查容器日志
docker-compose logs ququ-backend

# 检查GPU可用性
docker exec ququ-backend python3 -c "import torch; print(torch.cuda.is_available())"

# 检查FunASR安装
docker exec ququ-backend pip list | grep funasr

# 手动启动调试
docker exec -it ququ-backend bash
cd /workspace/ququ_backend
python3 server.py
```

### GPU不可用

```bash
# 检查宿主机GPU
nvidia-smi

# 检查Docker runtime
docker info | grep -i nvidia

# 检查容器GPU访问
docker exec ququ-backend nvidia-smi
```

### Ollama连接失败

```bash
# 检查宿主机Ollama
curl http://localhost:11434/v1/models

# 检查Ollama进程
ps aux | grep ollama

# 从容器测试连接
docker exec ququ-backend curl http://192.168.100.38:11434/v1/models
```

### FunASR模型未下载

```bash
# 下载模型（在容器内）
docker exec ququ-backend bash -c "
  cd /workspace/ququ &&
  python3 download_models.py
"

# 检查模型文件
docker exec ququ-backend ls -la ~/.cache/modelscope/hub/damo/
```

## 性能优化

### GPU加速效果

- **CPU模式**: ~5-10秒/分钟音频
- **GPU模式**: ~1-2秒/分钟音频（提升3-5倍）

### 并发配置

QuQu Backend当前配置为单worker，适合中等并发：
- 最大并发请求: 5-10
- GPU显存占用: ~4GB（FunASR模型）

如需提高并发：
1. 增加SERVER_WORKERS（需要更多GPU显存）
2. 实现请求队列
3. 配置负载均衡

### 内存管理

FunASR每10次转录自动清理内存：
```python
# funasr_gpu.py:240-243
if self.transcription_count % 10 == 0:
    self._cleanup_memory()
```

## 安全注意事项

1. **API访问控制**: 当前API无认证，生产环境应添加API Key
2. **CORS配置**: 当前允许所有来源，生产环境应限制域名
3. **文件上传**: 临时文件自动清理，但应监控磁盘空间
4. **GPU资源**: 多服务共享GPU时注意显存分配

## 相关文档

- **QuQu Backend**: `/data/deepresearch/ququ_backend/README.md`
- **QuQu原项目**: `/data/deepresearch/ququ/README.md`
- **DeepResearch**: `/data/deepresearch/DeepResearch/README.md`
- **项目总结**: `/data/deepresearch/PROJECT_SUMMARY.md`
- **安装指南**: `/data/deepresearch/INSTALLATION_GUIDE.md`

## 版本信息

- **PyTorch**: 2.4.0
- **CUDA**: 12.6
- **FunASR**: 1.2.7
- **FastAPI**: 0.115.0
- **Ollama**: 运行在宿主机
- **模型**: gpt-oss:20b (Ollama), Tongyi-DeepResearch-30B-A3B-Q4_K_M (llama.cpp)

## 常见问题

### Q: 如何添加新的API端点？
A: 在`/data/deepresearch/ququ_backend/server.py`中添加新的路由函数，参考现有的`@app.post()`示例。

### Q: 如何更换Ollama模型？
A: 修改docker-compose.yml中的`OLLAMA_MODEL`环境变量，或在请求时指定不同的模型。

### Q: 如何支持更多音频格式？
A: FunASR通过librosa加载音频，支持大多数常见格式（wav, mp3, m4a等）。如需特殊格式，可在server.py中添加音频转换逻辑。

### Q: 如何监控GPU使用情况？
A: 使用`nvidia-smi`或`watch -n 1 nvidia-smi`实时监控。容器内也可使用PyTorch的`torch.cuda.memory_summary()`。

### Q: 如何扩展到多GPU？
A: 修改`CUDA_VISIBLE_DEVICES`环境变量和docker-compose中的GPU配置，FunASR支持指定设备如`cuda:1`。

---

最后更新: 2025-10-15
