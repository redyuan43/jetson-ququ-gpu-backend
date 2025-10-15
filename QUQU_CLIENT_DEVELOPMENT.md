# QuQu客户端开发调试指南

## 📋 问题概述

QuQu客户端是Electron桌面应用，需要GUI环境进行开发和调试。后端已迁移到Jetson服务器的GPU加速服务。

## 🎯 开发方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **方案1: 本地开发机** | 开发体验最好、工具链完整、性能流畅 | 需要配置跨设备连接 | ⭐⭐⭐⭐⭐ |
| **方案2: Jetson本地GUI** | 网络延迟低、直接访问 | 需要显示器、开发工具安装麻烦 | ⭐⭐⭐ |
| **方案3: 远程桌面** | 灵活、可远程开发 | 网络延迟、性能损失 | ⭐⭐ |

## 🚀 推荐方案：本地开发机 + 远程后端

这是最佳的开发体验方案。

### 架构图

```
┌─────────────────────────────────────────────┐
│  本地开发机 (Windows/Mac/Linux)              │
│  192.168.100.X                              │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────┐      │
│  │  QuQu Electron 客户端            │      │
│  │  (开发模式)                       │      │
│  │                                   │      │
│  │  ┌──────────────┐                │      │
│  │  │ React UI     │                │      │
│  │  │ (Vite Dev)   │                │      │
│  │  └──────────────┘                │      │
│  │         │                         │      │
│  │  ┌──────▼───────┐                │      │
│  │  │ API Client   │                │      │
│  │  │ 配置后端地址  │                │      │
│  │  └──────┬───────┘                │      │
│  └─────────┼────────────────────────┘      │
│            │                                │
└────────────┼────────────────────────────────┘
             │
             │ HTTP API调用
             │ (192.168.100.38:8000)
             │
┌────────────▼────────────────────────────────┐
│  Jetson AGX Orin Server                     │
│  192.168.100.38                             │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────┐      │
│  │  ququ-backend (Docker)           │      │
│  │                                   │      │
│  │  ┌─────────────┐  ┌────────────┐│      │
│  │  │ FastAPI     │  │ FunASR GPU ││      │
│  │  │ :8000       │──│ + Ollama   ││      │
│  │  └─────────────┘  └────────────┘│      │
│  └──────────────────────────────────┘      │
│                                             │
└─────────────────────────────────────────────┘
```

### 步骤1: 准备本地开发环境

#### Windows开发环境

```powershell
# 1. 安装Node.js (推荐v20 LTS)
# 下载: https://nodejs.org/

# 2. 安装pnpm
npm install -g pnpm

# 3. 克隆QuQu项目（如果还没有）
git clone https://github.com/yan5xu/ququ.git
cd ququ

# 4. 安装依赖
pnpm install
```

#### macOS开发环境

```bash
# 1. 安装Homebrew（如果还没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 安装Node.js
brew install node

# 3. 安装pnpm
npm install -g pnpm

# 4. 克隆并安装
git clone https://github.com/yan5xu/ququ.git
cd ququ
pnpm install
```

#### Linux (Ubuntu/Debian) 开发环境

```bash
# 1. 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# 2. 安装pnpm
npm install -g pnpm

# 3. 克隆并安装
git clone https://github.com/yan5xu/ququ.git
cd ququ
pnpm install
```

### 步骤2: 修改QuQu客户端连接远程后端

QuQu原本使用内嵌的Python FunASR服务，现在需要修改为连接远程API。

#### 2.1 创建后端API配置文件

创建 `src/config/backend.js`:

```javascript
// src/config/backend.js
/**
 * QuQu后端API配置
 * 用于连接Jetson GPU加速后端服务
 */

// 开发环境配置
const DEVELOPMENT_CONFIG = {
  // Jetson服务器地址
  baseURL: 'http://192.168.100.38:8000',
  timeout: 30000, // 30秒超时

  // API端点
  endpoints: {
    health: '/api/health',
    status: '/api/status',
    transcribe: '/api/asr/transcribe',
    optimize: '/api/llm/optimize',
    transcribeAndOptimize: '/api/asr/transcribe-and-optimize'
  }
};

// 生产环境配置（打包后使用localhost或配置的地址）
const PRODUCTION_CONFIG = {
  baseURL: process.env.BACKEND_URL || 'http://localhost:8000',
  timeout: 30000,
  endpoints: DEVELOPMENT_CONFIG.endpoints
};

// 根据环境导出配置
const config = process.env.NODE_ENV === 'production'
  ? PRODUCTION_CONFIG
  : DEVELOPMENT_CONFIG;

export default config;

// 辅助函数：获取完整URL
export function getEndpointURL(endpointName) {
  return config.baseURL + config.endpoints[endpointName];
}

// 辅助函数：检查后端健康状态
export async function checkBackendHealth() {
  try {
    const response = await fetch(getEndpointURL('health'), {
      method: 'GET',
      timeout: 5000
    });
    return response.ok;
  } catch (error) {
    console.error('Backend health check failed:', error);
    return false;
  }
}
```

#### 2.2 创建API客户端封装

创建 `src/services/backendAPI.js`:

```javascript
// src/services/backendAPI.js
/**
 * QuQu后端API客户端
 * 封装与GPU加速后端的通信
 */

import axios from 'axios';
import backendConfig, { getEndpointURL } from '../config/backend.js';

// 创建axios实例
const apiClient = axios.create({
  baseURL: backendConfig.baseURL,
  timeout: backendConfig.timeout,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器
apiClient.interceptors.request.use(
  config => {
    console.log(`[API] ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  error => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  response => {
    console.log(`[API] Response:`, response.status);
    return response;
  },
  error => {
    console.error('[API] Response error:', error.response?.status, error.message);
    return Promise.reject(error);
  }
);

/**
 * 语音识别API
 * @param {Blob|File} audioBlob - 音频数据
 * @param {Object} options - 识别选项
 * @returns {Promise<Object>} 识别结果
 */
export async function transcribeAudio(audioBlob, options = {}) {
  const {
    useVad = true,
    usePunc = true,
    hotword = ''
  } = options;

  const formData = new FormData();
  formData.append('audio', audioBlob, 'audio.wav');
  formData.append('use_vad', useVad);
  formData.append('use_punc', usePunc);
  formData.append('hotword', hotword);

  try {
    const response = await apiClient.post(
      backendConfig.endpoints.transcribe,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    );

    return response.data;
  } catch (error) {
    console.error('Transcription failed:', error);
    throw error;
  }
}

/**
 * 文本优化API
 * @param {string} text - 待优化文本
 * @param {string} mode - 优化模式 (optimize/format/punctuate/custom)
 * @param {string} customPrompt - 自定义提示词（mode为custom时使用）
 * @returns {Promise<Object>} 优化结果
 */
export async function optimizeText(text, mode = 'optimize', customPrompt = null) {
  try {
    const response = await apiClient.post(
      backendConfig.endpoints.optimize,
      {
        text,
        mode,
        custom_prompt: customPrompt
      }
    );

    return response.data;
  } catch (error) {
    console.error('Text optimization failed:', error);
    throw error;
  }
}

/**
 * 一体化处理API（语音识别 + 文本优化）
 * @param {Blob|File} audioBlob - 音频数据
 * @param {Object} options - 处理选项
 * @returns {Promise<Object>} 处理结果
 */
export async function transcribeAndOptimize(audioBlob, options = {}) {
  const {
    useVad = true,
    usePunc = true,
    hotword = '',
    optimizeMode = 'optimize'
  } = options;

  const formData = new FormData();
  formData.append('audio', audioBlob, 'audio.wav');
  formData.append('use_vad', useVad);
  formData.append('use_punc', usePunc);
  formData.append('hotword', hotword);
  formData.append('optimize_mode', optimizeMode);

  try {
    const response = await apiClient.post(
      backendConfig.endpoints.transcribeAndOptimize,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    );

    return response.data;
  } catch (error) {
    console.error('Transcribe and optimize failed:', error);
    throw error;
  }
}

/**
 * 获取后端状态
 * @returns {Promise<Object>} 后端状态信息
 */
export async function getBackendStatus() {
  try {
    const response = await apiClient.get(backendConfig.endpoints.status);
    return response.data;
  } catch (error) {
    console.error('Failed to get backend status:', error);
    throw error;
  }
}

/**
 * 健康检查
 * @returns {Promise<boolean>} 后端是否健康
 */
export async function healthCheck() {
  try {
    const response = await apiClient.get(backendConfig.endpoints.health);
    return response.status === 200;
  } catch (error) {
    return false;
  }
}

export default {
  transcribeAudio,
  optimizeText,
  transcribeAndOptimize,
  getBackendStatus,
  healthCheck
};
```

#### 2.3 修改QuQu原有代码

找到QuQu中调用FunASR的地方（可能在`main.js`或`src`目录下），替换为调用上面的API。

**示例修改（伪代码）：**

```javascript
// 原来的代码（调用本地Python）
// const result = await callLocalFunASR(audioData);

// 修改为调用远程API
import { transcribeAudio } from './services/backendAPI.js';

// 在录音结束后
async function handleAudioRecorded(audioBlob) {
  try {
    // 显示加载状态
    setLoading(true);

    // 调用远程GPU加速后端
    const result = await transcribeAudio(audioBlob, {
      useVad: true,
      usePunc: true,
      hotword: userHotwords
    });

    if (result.success) {
      // 显示识别结果
      displayText(result.text);
    } else {
      showError('识别失败: ' + result.error);
    }
  } catch (error) {
    showError('网络错误: ' + error.message);
  } finally {
    setLoading(false);
  }
}
```

### 步骤3: 配置环境变量

创建 `.env` 文件（在QuQu项目根目录）:

```bash
# QuQu客户端环境配置

# 后端API地址
BACKEND_URL=http://192.168.100.38:8000

# 开发模式
NODE_ENV=development
DEBUG=true
LOG_LEVEL=debug

# 其他配置（保留原有配置）
LANGUAGE=zh-CN
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1
AUDIO_FORMAT=wav
THEME=auto
GLOBAL_HOTKEY=CommandOrControl+Shift+Space
```

### 步骤4: 启动开发服务器

```bash
# 在QuQu项目目录
cd ququ

# 启动开发模式（热重载）
pnpm run dev

# 或者直接运行Electron
pnpm start
```

Electron窗口会自动打开，此时QuQu客户端会连接到Jetson服务器的GPU加速后端。

### 步骤5: 开发调试

#### 5.1 Chrome DevTools调试

Electron应用可以使用Chrome DevTools：

```javascript
// 在main.js中添加（开发模式）
if (process.env.NODE_ENV === 'development') {
  mainWindow.webContents.openDevTools();
}
```

快捷键：
- **Windows/Linux**: `Ctrl + Shift + I`
- **macOS**: `Cmd + Option + I`

#### 5.2 查看网络请求

在DevTools的Network标签中可以看到所有API调用：
- 请求URL: `http://192.168.100.38:8000/api/asr/transcribe`
- 请求方法: POST
- 响应时间
- 响应内容

#### 5.3 后端日志监控

在另一个终端监控Jetson后端日志：

```bash
# SSH连接到Jetson
ssh agx@192.168.100.38

# 实时查看后端日志
docker-compose logs -f ququ-backend
```

### 步骤6: 测试完整流程

#### 测试清单

- [ ] 后端健康检查
- [ ] 语音录制
- [ ] 音频上传
- [ ] 语音识别返回
- [ ] 文本优化（如果使用）
- [ ] 结果显示
- [ ] 错误处理

#### 快速测试脚本

创建 `test-backend-connection.js`:

```javascript
// test-backend-connection.js
/**
 * 测试QuQu客户端与后端连接
 */

const axios = require('axios');

const BACKEND_URL = 'http://192.168.100.38:8000';

async function testConnection() {
  console.log('🔍 测试QuQu后端连接...\n');

  // 1. 健康检查
  console.log('1️⃣  测试健康检查...');
  try {
    const health = await axios.get(`${BACKEND_URL}/api/health`);
    console.log('   ✅ 健康检查通过:', health.data);
  } catch (error) {
    console.error('   ❌ 健康检查失败:', error.message);
    return;
  }

  // 2. 状态检查
  console.log('\n2️⃣  测试状态查询...');
  try {
    const status = await axios.get(`${BACKEND_URL}/api/status`);
    console.log('   ✅ 后端状态:');
    console.log('      FunASR:', status.data.funasr.initialized ? '已初始化' : '未初始化');
    console.log('      Ollama:', status.data.ollama.available ? '可用' : '不可用');
    console.log('      GPU:', status.data.gpu_available ? '可用' : '不可用');
  } catch (error) {
    console.error('   ❌ 状态查询失败:', error.message);
    return;
  }

  // 3. 文本优化测试
  console.log('\n3️⃣  测试文本优化...');
  try {
    const optimize = await axios.post(`${BACKEND_URL}/api/llm/optimize`, {
      text: '这个嗯那个就是说测试一下',
      mode: 'optimize'
    });
    console.log('   ✅ 文本优化成功:');
    console.log('      原文:', optimize.data.original_text);
    console.log('      优化后:', optimize.data.optimized_text);
  } catch (error) {
    console.error('   ❌ 文本优化失败:', error.message);
  }

  console.log('\n✅ 所有测试完成！QuQu客户端可以连接到后端。');
}

testConnection().catch(console.error);
```

运行测试：

```bash
node test-backend-connection.js
```

## 🔧 方案2: Jetson本地GUI开发

如果您有显示器可以连接Jetson，也可以直接在Jetson上开发。

### 步骤1: 安装桌面环境（如果还没有）

```bash
# 安装轻量级桌面环境XFCE
sudo apt update
sudo apt install xfce4 xfce4-goodies

# 或安装完整的Ubuntu Desktop
sudo apt install ubuntu-desktop
```

### 步骤2: 连接显示器启动GUI

```bash
# 启动桌面环境
startx
```

### 步骤3: 在Jetson上安装开发工具

```bash
# 安装Node.js和pnpm（如果还没有）
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g pnpm

# 安装VS Code（可选）
sudo snap install code --classic
```

### 步骤4: 克隆和开发

```bash
cd /data/deepresearch/ququ
pnpm install
pnpm run dev
```

此时QuQu会在本地运行，后端也在localhost:8000，延迟最低。

## 🌐 方案3: 远程桌面/VNC

适合需要远程开发的场景。

### 步骤1: 在Jetson上安装VNC服务器

```bash
# 安装x11vnc
sudo apt update
sudo apt install x11vnc

# 创建VNC密码
x11vnc -storepasswd

# 启动VNC服务器
x11vnc -display :0 -auth /var/run/lightdm/root/:0 -forever -loop -noxdamage -repeat -rfbauth ~/.vnc/passwd -rfbport 5900 -shared
```

### 步骤2: 从本地连接

**Windows:**
- 使用 RealVNC Viewer 或 TigerVNC
- 连接到: `192.168.100.38:5900`

**macOS:**
- 内置"屏幕共享"应用
- 或使用 RealVNC Viewer

**Linux:**
```bash
# 使用Remmina或VNC客户端
sudo apt install remmina
```

### 步骤3: 在远程桌面中开发

连接后就像在本地一样操作Jetson的桌面环境。

## 📊 方案对比总结

| 项目 | 方案1: 本地开发 | 方案2: Jetson GUI | 方案3: 远程桌面 |
|------|----------------|------------------|----------------|
| 开发流畅度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 网络延迟 | 有（API调用） | 无 | 有（远程桌面） |
| 配置复杂度 | 中 | 高 | 中 |
| 硬件需求 | 开发机 | 显示器+键鼠 | 开发机 |
| 调试便利性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

## 💡 最佳实践建议

1. **推荐使用方案1**（本地开发机 + 远程后端）
   - 开发体验最好
   - 工具链完整
   - 便于版本控制

2. **开发流程：**
   ```
   本地编写代码 → 热重载测试 → Git提交 →
   部署到生产环境（如需）
   ```

3. **调试技巧：**
   - 使用Chrome DevTools查看网络请求
   - 监控后端日志了解API响应
   - 使用Postman/curl测试API独立于客户端

4. **代码管理：**
   - Fork原QuQu仓库
   - 创建feature分支进行修改
   - 提交PR回馈社区

## 🚨 常见问题

**Q: API调用超时？**
```javascript
// 增加超时时间
axios.create({
  timeout: 60000 // 60秒
});
```

**Q: CORS错误？**
后端已配置允许跨域，如果还有问题，检查：
```yaml
# docker-compose.yml中确认
environment:
  - CORS_ORIGINS=*  # 或具体的客户端地址
```

**Q: 音频格式不支持？**
确保音频格式为wav，采样率16000Hz：
```javascript
// 转换音频格式
const audioContext = new AudioContext({ sampleRate: 16000 });
```

**Q: 网络慢怎么办？**
- 使用局域网有线连接
- 压缩音频数据
- 考虑批处理请求

## 📚 相关文档

- QuQu原项目: https://github.com/yan5xu/ququ
- Electron文档: https://www.electronjs.org/docs
- 后端API文档: http://192.168.100.38:8000/docs
- 本项目文档: [DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md)

---

**祝您开发顺利！如有问题，请参考文档或在GitHub提Issue。** 🎉
