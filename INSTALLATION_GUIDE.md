# 🛠️ Jetson AGX Orin DeepResearch 完整安装指南

## 📋 安装步骤总结

### 第一阶段：环境准备（关键步骤）

#### 1. 系统环境检查
```bash
# 检查Jetson硬件和系统版本
uname -a                          # 确认Linux 5.15.148-tegra
nvidia-smi                        # 验证GPU驱动和CUDA 12.6
free -h                           # 检查内存（应有64GB）
df -h                             # 检查磁盘空间（模型需要20GB+）
```

#### 2. 安装必要工具
```bash
# 安装基础工具
sudo apt update && sudo apt install -y \
    git wget curl vim htop tree \
    build-essential cmake \
    python3-pip python3-dev

# 安装Docker（如果未安装）
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

#### 3. 配置Huggingface访问
```bash
# 安装huggingface-cli
pip install --upgrade huggingface_hub

# 登录（必需步骤）
huggingface-cli login
# 输入你的access token
```

### 第二阶段：获取llama.cpp（容器方案）

#### 方案A：使用现有容器（推荐）
```bash
# 检查现有容器
docker images | grep jetson
docker ps -a | grep jetson

# 如果有现成的PyTorch+CUDA容器，直接使用
# 例如：jetson_minicpm_v:latest
```

#### 方案B：手动编译llama.cpp
```bash
# 克隆llama.cpp
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp

# 编译CUDA版本
make -j$(nproc) LLAMA_CUDA=1

# 验证编译结果
ls -la build/bin/llama-cli build/bin/llama-server
```

### 第三阶段：模型下载（关键）

#### 1. 创建模型目录
```bash
mkdir -p /data/sensor-voice/models
cd /data/sensor-voice/models
```

#### 2. 下载Q4_K_M模型（18GB）
```bash
# 使用huggingface-cli下载（已登录状态下）
huggingface-cli download \
  bartowski/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-GGUF \
  Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf \
  --local-dir .

# 验证下载
ls -lh Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf
```

#### 3. 备选下载方案
```bash
# 如果主链接失败，尝试备选源
# 方案1: 其他GGUF仓库
huggingface-cli download \
  gabriellarson/Tongyi-DeepResearch-30B-A3B-GGUF \
  tongyi-deepresearch-30b-a3b.Q4_K_M.gguf \
  --local-dir .

# 方案2: 使用git-lfs（需要安装git-lfs）
git lfs install
git clone https://huggingface.co/bartowski/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-GGUF
```

### 第四阶段：Docker环境配置

#### 1. 创建docker-compose.yml
```bash
# 创建工作目录
mkdir -p /data/deepresearch
cd /data/deepresearch

# 创建docker-compose.yml文件（内容见附录A）
# 或使用已提供的文件
```

#### 2. 创建启动脚本
```bash
# 一键启动脚本（内容见附录B）
# 或使用已提供的start.sh
```

#### 3. 测试Docker环境
```bash
# 启动基础容器
docker-compose up -d jetson-deepresearch

# 检查状态
docker-compose ps

# 进入容器测试
docker-compose exec jetson-deepresearch bash
```

### 第五阶段：验证测试

#### 1. 环境验证
```bash
# 在容器内测试PyTorch CUDA
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# 测试llama.cpp
export LD_LIBRARY_PATH=/workspace/llama.cpp/build/bin:$LD_LIBRARY_PATH
/workspace/llama.cpp/build/bin/llama-cli --version
```

#### 2. 模型验证
```bash
# 快速模型测试
export LD_LIBRARY_PATH=/workspace/llama.cpp/build/bin:$LD_LIBRARY_PATH
/workspace/llama.cpp/build/bin/llama-cli \
  --model /workspace/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf \
  --ctx-size 512 \
  --n-gpu-layers 10 \
  --predict 10 \
  --prompt "测试" \
  --no-display-prompt
```

#### 3. 服务器测试
```bash
# 启动服务器
/workspace/llama.cpp/build/bin/llama-server \
  --model /workspace/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf \
  --ctx-size 8192 \
  --n-gpu-layers 35 \
  --port 8080 \
  --host 0.0.0.0

# 测试API
curl http://localhost:8080/v1/models
```

## ⚠️ 关键注意事项

### 1. 硬件要求检查
- **内存**: 必须≥32GB，推荐64GB（AGX Orin）
- **存储**: 至少50GB可用空间（模型18GB + 缓存）
- **GPU**: 必须支持CUDA，计算能力≥7.0

### 2. 网络配置
- **Huggingface访问**: 需要稳定的网络连接
- **代理设置**: 如需要，配置HTTP_PROXY/HTTPS_PROXY
- **DNS**: 确保能解析huggingface.co

### 3. 权限问题
```bash
# Docker权限
sudo usermod -aG docker $USER
# 重新登录生效

# 文件权限
sudo chown -R $USER:$USER /data/sensor-voice
```

### 4. 内存优化
```bash
# 关闭不必要的服务
sudo systemctl stop gdm3  # 关闭GUI（可选）
sudo systemctl set-default multi-user.target

# 增加交换空间（如果需要）
sudo fallocate -l 16G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 5. 性能调优
```bash
# GPU内存分配
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

# llama.cpp优化
export GGML_CUDA=1
export LLAMA_CUDA=1

# Jetson特定优化
export CUDA_ARCH_LIST=8.7
```

## 🚨 常见错误及解决方案

### 错误1: HuggingFace认证失败
```
401 Unauthorized
```
**解决**:
```bash
# 重新登录
huggingface-cli logout
huggingface-cli login
# 确保token有效
```

### 错误2: CUDA不可用
```
CUDA available: False
```
**解决**:
```bash
# 检查NVIDIA驱动
nvidia-smi
# 检查容器运行时
docker info | grep -i nvidia
# 确保使用nvidia-runtime
```

### 错误3: 模型文件损坏
```
failed to load model
```
**解决**:
```bash
# 重新下载
rm /data/sensor-voice/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf
huggingface-cli download ...
# 验证文件大小（应为18GB）
ls -lh /data/sensor-voice/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf
```

### 错误4: 内存不足
```
out of memory
```
**解决**:
```bash
# 减少GPU层数--n-gpu-layers 20
# 减小上下文--ctx-size 4096
# 增加交换空间
# 关闭其他应用
```

### 错误5: 库文件缺失
```
libllama.so: cannot open shared object file
```
**解决**:
```bash
export LD_LIBRARY_PATH=/path/to/llama.cpp/build/bin:$LD_LIBRARY_PATH
```

## 📊 验证清单

### 安装前检查
- [ ] 系统版本确认（Linux 5.15.148-tegra）
- [ ] CUDA版本确认（12.6）
- [ ] 内存检查（≥32GB）
- [ ] 磁盘空间检查（≥50GB）
- [ ] 网络连接测试

### 安装过程检查
- [ ] HuggingFace登录成功
- [ ] Docker运行正常
- [ ] 模型下载完整（18GB）
- [ ] llama.cpp编译成功
- [ ] PyTorch CUDA可用

### 功能测试
- [ ] 模型加载测试通过
- [ ] 基础推理测试通过
- [ ] API服务器启动成功
- [ ] 容器环境稳定运行

## 🔧 快速故障排查脚本

创建`troubleshoot.sh`:
```bash
#!/bin/bash
echo "🔍 Jetson DeepResearch 故障排查..."
echo "1️⃣ 系统信息:"
uname -a
echo "2️⃣ GPU状态:"
nvidia-smi 2>/dev/null || echo "❌ nvidia-smi不可用"
echo "3️⃣ Docker状态:"
docker info | grep -i nvidia
echo "4️⃣ 模型文件:"
ls -lh /data/sensor-voice/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf 2>/dev/null || echo "❌ 模型文件不存在"
echo "5️⃣ llama.cpp:"
ls -la /data/sensor-voice/sensor-voice/llama.cpp/build/bin/llama-cli 2>/dev/null || echo "❌ llama-cli不存在"
echo "6️⃣ HuggingFace:"
huggingface-cli whoami 2>/dev/null || echo "❌ 未登录HuggingFace"
```

## 📚 附录

### 附录A: docker-compose.yml模板
```yaml
version: '3.8'
services:
  jetson-deepresearch:
    image: jetson_minicpm_v:latest
    container_name: deepresearch
    runtime: nvidia
    network_mode: host
    environment:
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics
      - CUDA_VISIBLE_DEVICES=0
      - LLAMA_CUDA=1
    volumes:
      - /data/sensor-voice:/workspace
      - /data/sensor-voice/models:/workspace/models
      - /data/sensor-voice/sensor-voice/llama.cpp:/workspace/llama.cpp
    working_dir: /workspace
    command: /bin/bash
    stdin_open: true
    tty: true
```

### 附录B: 一键启动脚本
```bash
#!/bin/bash
echo "🚀 启动 Jetson DeepResearch..."
docker-compose up -d jetson-deepresearch
sleep 10
docker-compose ps
```

这个指南总结了所有成功的安装步骤和注意事项，你可以在任何Jetson AGX Orin环境中按照这个标准化流程进行部署。需要我补充任何特定的细节吗？