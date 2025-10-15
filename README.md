# Jetson QuQu GPU Backend

> 基于Jetson AGX Orin的GPU加速QuQu语音识别后端服务

[![GitHub](https://img.shields.io/badge/GitHub-redyuan43-blue?logo=github)](https://github.com/redyuan43/jetson-ququ-gpu-backend)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-nvidia--runtime-blue?logo=docker)](https://www.docker.com/)
[![CUDA](https://img.shields.io/badge/CUDA-12.6-green?logo=nvidia)](https://developer.nvidia.com/cuda-toolkit)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📖 项目简介

将[QuQu](https://github.com/yan5xu/ququ)项目的FunASR语音识别后端改造为基于Jetson AGX Orin GPU加速的服务端架构，支持局域网多客户端访问。集成Ollama LLM进行文本优化处理。

### ✨ 核心特性

- 🚀 **GPU加速**: FunASR模型运行在CUDA GPU上，性能提升3-5倍
- 🌐 **API服务**: FastAPI构建的RESTful接口，支持多客户端并发访问
- 🤖 **LLM集成**: Ollama文本优化（删除口头禅、格式化、添加标点）
- 🐳 **容器化**: Docker部署，开箱即用
- ⚡ **开机自启**: 配置完成后自动启动，无需人工干预
- 💾 **模型缓存**: 持久化存储，避免重复下载

## 🎯 性能指标

| 指标 | CPU模式 | GPU模式 | 提升 |
|------|---------|---------|------|
| 1分钟音频识别 | 5-10秒 | 1-2秒 | **3-5倍** |
| 模型加载时间 | 60-90秒 | 17秒 | **4-5倍** |
| GPU显存占用 | 0GB | ~4GB | - |
| 并发能力 | 低 | 中高 | - |

## 🏗️ 技术架构

### 技术栈

| 组件 | 版本 | 说明 |
|------|------|------|
| 硬件平台 | Jetson AGX Orin 64GB | NVIDIA Ampere GPU |
| 操作系统 | Ubuntu 20.04 | Linux 5.15.148-tegra |
| CUDA | 12.6 | GPU计算平台 |
| PyTorch | 2.4.0 | 深度学习框架 |
| FunASR | 1.2.7 | 阿里达摩院语音识别 |
| FastAPI | 0.115.0 | Web框架 |
| Ollama | 本地部署 | LLM推理引擎 |
| Docker | nvidia-runtime | 容器运行时 |

### 架构图

```
┌─────────────────────────────────────────────┐
│        Jetson AGX Orin Server               │
│         (192.168.100.38)                    │
├─────────────────────────────────────────────┤
│                                             │
│  ┌────────────────────────────────────┐    │
│  │  宿主机 (Host)                      │    │
│  │                                    │    │
│  │  ┌──────────┐   ┌──────────────┐  │    │
│  │  │ Ollama   │   │ DeepResearch │  │    │
│  │  │ :11434   │   │ 模型/工具    │  │    │
│  │  └──────────┘   └──────────────┘  │    │
│  └────────────────────────────────────┘    │
│           │                                 │
│  ┌────────▼───────────────────────────┐    │
│  │  Docker: ququ-backend              │    │
│  │                                     │    │
│  │  ┌──────────┐  ┌──────────────┐   │    │
│  │  │ FastAPI  │  │ FunASR GPU   │   │    │
│  │  │ :8000    │──│ ASR/VAD/PUNC │   │    │
│  │  └──────────┘  └──────────────┘   │    │
│  └─────────────────────────────────────┘    │
│           │                                 │
└───────────┼─────────────────────────────────┘
            │
      ┌─────┴─────┐
      │           │
 ┌────▼───┐  ┌───▼────┐
 │ QuQu   │  │ QuQu   │
 │Client 1│  │Client N│
 └────────┘  └────────┘
```

## 🚀 快速开始

### 前置要求

- Jetson AGX Orin（或其他支持CUDA的Jetson设备）
- 已安装Docker with nvidia runtime
- 已安装Ollama并运行（可选，用于文本优化）

### 一键启动

```bash
# 克隆仓库
git clone https://github.com/redyuan43/jetson-ququ-gpu-backend.git
cd jetson-ququ-gpu-backend

# 启动服务
./start-ququ-backend.sh
```

等待约17秒模型加载完成，服务即可使用。

### 手动启动

```bash
# 启动容器
docker-compose up -d ququ-backend

# 查看日志
docker-compose logs -f ququ-backend

# 检查健康状态
curl http://localhost:8000/api/health
```

## 📡 API使用

### 服务地址

- **本地访问**: http://localhost:8000
- **局域网访问**: http://192.168.100.38:8000
- **API文档**: http://192.168.100.38:8000/docs

### API端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/status` | GET | 服务状态 |
| `/api/asr/transcribe` | POST | 语音识别 |
| `/api/llm/optimize` | POST | 文本优化 |
| `/api/asr/transcribe-and-optimize` | POST | 一体化处理 |

### 使用示例

#### 1. 语音识别

```bash
curl -X POST http://192.168.100.38:8000/api/asr/transcribe \
  -F "audio=@test.wav" \
  -F "use_vad=true" \
  -F "use_punc=true"
```

响应示例：
```json
{
  "success": true,
  "text": "今天天气很好，我们去公园散步吧。",
  "raw_text": "今天天气很好我们去公园散步吧",
  "duration": 3.5,
  "language": "zh-CN"
}
```

#### 2. 文本优化

```bash
curl -X POST http://192.168.100.38:8000/api/llm/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "这个嗯那个就是说我们今天要开会",
    "mode": "optimize"
  }'
```

响应示例：
```json
{
  "success": true,
  "original_text": "这个嗯那个就是说我们今天要开会",
  "optimized_text": "我们今天要开会。",
  "mode": "optimize",
  "model": "gpt-oss:20b"
}
```

## 🔧 配置说明

### 环境变量

在 `docker-compose.yml` 中可配置：

```yaml
environment:
  - CUDA_VISIBLE_DEVICES=0          # GPU设备ID
  - OLLAMA_BASE_URL=http://localhost:11434  # Ollama地址
  - OLLAMA_MODEL=gpt-oss:20b        # LLM模型名称
  - SERVER_PORT=8000                # API端口
  - SERVER_WORKERS=1                # 工作进程数
```

### 模型缓存

模型缓存持久化到宿主机，避免重复下载：

```yaml
volumes:
  - /data/deepresearch/modelscope_cache:/root/.cache/modelscope
```

缓存大小约2GB，包含：
- ASR模型（Paraformer-large）: 840MB
- VAD模型（FSMN-VAD）: 278MB
- PUNC模型（CT-Transformer）: 小于100MB

## 🎛️ 开机自启

服务已配置为开机自启动：

```bash
# 检查自启配置
./check-autostart.sh
```

启动流程：
1. 设备开机 (~30秒)
2. Docker服务启动 (~5秒)
3. 容器自动启动 (~2秒)
4. FunASR模型加载 (~17秒)
5. **总计约54秒后服务就绪**

详见 [AUTOSTART.md](./AUTOSTART.md)

## 📚 文档

- [DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md) - 完整部署总结
- [AUTOSTART.md](./AUTOSTART.md) - 开机自启配置
- [CLAUDE.md](./CLAUDE.md) - Claude Code项目指南
- [GIT_REPORT.md](./GIT_REPORT.md) - Git提交报告
- [ququ_backend/README.md](./ququ_backend/README.md) - 后端API详细文档

## 🔍 故障排查

### 常见问题

**Q: GPU不可用？**
```bash
# 检查nvidia-smi
nvidia-smi

# 检查Docker GPU运行时
docker info | grep -i nvidia

# 重启容器
docker-compose restart ququ-backend
```

**Q: Ollama连接失败？**
```bash
# 检查Ollama服务
curl http://localhost:11434/v1/models

# 从容器内测试
docker exec ququ-backend curl http://localhost:11434/v1/models
```

**Q: 模型加载缓慢？**
```bash
# 检查模型缓存
du -sh /data/deepresearch/modelscope_cache
# 应该显示约2.0GB

# 如果为空，模型会自动下载
```

更多问题请参考 [DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md)

## 🛠️ 开发

### 项目结构

```
.
├── ququ_backend/           # 后端服务代码
│   ├── server.py           # FastAPI主服务
│   ├── funasr_gpu.py      # GPU加速FunASR
│   ├── llm_client.py      # Ollama客户端
│   ├── test_gpu.py        # GPU测试脚本
│   └── requirements.txt   # Python依赖
├── docker-compose.yml      # Docker配置
├── start-ququ-backend.sh  # 启动脚本
├── check-autostart.sh     # 自启检查脚本
└── 文档/                   # 完整文档
```

### 测试GPU加速

```bash
docker exec -it ququ-backend bash
cd /workspace/ququ_backend
python3 test_gpu.py
```

应该看到所有5个测试通过。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可

本项目基于以下开源项目：

- [QuQu](https://github.com/yan5xu/ququ) - 原始QuQu客户端项目
- [DeepResearch](https://github.com/Alibaba-NLP/DeepResearch) - 阿里巴巴通义DeepResearch
- [FunASR](https://github.com/alibaba-damo-academy/FunASR) - 达摩院语音识别框架

## 🙏 致谢

- QuQu项目作者 [@yan5xu](https://github.com/yan5xu)
- 阿里巴巴达摩院 FunASR团队
- Ollama开源社区

## 📮 联系方式

- GitHub: [@redyuan43](https://github.com/redyuan43)
- 项目主页: https://github.com/redyuan43/jetson-ququ-gpu-backend

---

**⭐ 如果这个项目对您有帮助，请给一个Star！**
