# QuQu Backend - GPU加速语音识别服务

## 项目简介

基于Jetson AGX Orin的GPU加速FunASR语音识别后端服务，为QuQu客户端提供局域网API访问。

## 技术栈

- **语音识别**: FunASR 1.2.7 (GPU加速)
- **API框架**: FastAPI
- **LLM集成**: Ollama (本地部署)
- **硬件平台**: Jetson AGX Orin (CUDA 12.6)
- **容器**: jetson_minicpm_v:latest

## 架构设计

```
客户端 (局域网)
    ↓ HTTP POST /api/asr/transcribe
[QuQu Backend Server]
    ├─ FunASR (GPU加速识别)
    └─ Ollama (文本优化) → 宿主机:11434
```

## API端点

### 1. 语音识别
```bash
POST /api/asr/transcribe
Content-Type: multipart/form-data

# 参数
- audio: 音频文件
- use_vad: 是否使用VAD (默认true)
- use_punc: 是否添加标点 (默认true)
- hotword: 热词 (可选)

# 响应
{
  "success": true,
  "text": "识别的文本内容",
  "duration": 2.5,
  "language": "zh-CN"
}
```

### 2. 文本优化
```bash
POST /api/llm/optimize
Content-Type: application/json

{
  "text": "原始文本",
  "mode": "optimize"  # optimize/format/custom
}

# 响应
{
  "success": true,
  "original_text": "原始文本",
  "optimized_text": "优化后的文本"
}
```

### 3. 服务状态
```bash
GET /api/status

# 响应
{
  "success": true,
  "funasr_initialized": true,
  "gpu_available": true,
  "models_loaded": {
    "asr": true,
    "vad": true,
    "punc": true
  }
}
```

## 部署方式

### 使用Docker Compose

```bash
# 1. 确保在deepresearch目录
cd /data/deepresearch

# 2. 启动服务
docker-compose up -d ququ-backend

# 3. 查看日志
docker-compose logs -f ququ-backend

# 4. 测试服务
curl http://192.168.100.38:8000/api/status
```

### 性能指标

- **GPU加速**: 3-5倍于CPU性能提升
- **并发支持**: 最多5个并发请求
- **识别速度**: ~1-2秒/分钟音频
- **GPU显存**: ~4GB（模型加载）

## 环境要求

- Jetson AGX Orin (或同等CUDA设备)
- CUDA 12.6+
- PyTorch 2.4.0+
- FunASR 1.2.7+
- 宿主机运行Ollama服务

## 配置说明

### 环境变量

```bash
# GPU设备
CUDA_VISIBLE_DEVICES=0

# Ollama地址
OLLAMA_BASE_URL=http://localhost:11434/v1

# 服务端口
SERVER_PORT=8000

# 日志级别
LOG_LEVEL=INFO
```

## 客户端配置

修改QuQu客户端配置，指向后端服务：

```javascript
// 配置文件
const BACKEND_CONFIG = {
  baseURL: "http://192.168.100.38:8000",  // Jetson服务器IP
  timeout: 30000
};
```

## 故障排查

### GPU不可用
```bash
# 检查CUDA
nvidia-smi

# 检查容器GPU
docker exec ququ-backend python3 -c "import torch; print(torch.cuda.is_available())"
```

### FunASR模型未下载
```bash
# 下载模型
docker exec ququ-backend python3 /workspace/ququ/download_models.py
```

### Ollama无法连接
```bash
# 检查宿主机Ollama
curl http://localhost:11434/v1/models

# 确认网络连通性
docker exec ququ-backend curl http://host.docker.internal:11434/v1/models
```

## 开发说明

### 项目结构
```
ququ_backend/
├── server.py           # FastAPI主服务
├── funasr_gpu.py      # GPU版FunASR管理器
├── llm_client.py      # Ollama客户端
├── requirements.txt   # Python依赖
└── README.md          # 本文档
```

### 本地测试
```bash
# 进入容器
docker exec -it ququ-backend bash

# 启动服务
cd /workspace/ququ_backend
python3 server.py

# 测试API
curl -X POST http://localhost:8000/api/asr/transcribe \
  -F "audio=@test.wav"
```

## 许可证

Apache 2.0 License
