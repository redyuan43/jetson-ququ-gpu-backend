# 🚀 QuQu Backend API 快速参考

## 📋 所有API端点一览

### 流式API（实时反馈）✨

| 端点 | 功能 | 测试命令 |
|------|------|----------|
| `/api/asr/transcribe-and-optimize-stream` | ASR + 文本优化 | `python test_stream_api.py test.mp3` |
| `/api/asr/transcribe-and-translate-stream` | ASR + 翻译 | `python test_stream_translate_api.py test.mp3 中文 英文` |

### 传统API（一次性返回）

| 端点 | 功能 | 用途 |
|------|------|------|
| `/api/asr/transcribe` | 仅ASR识别 | 快速转录 |
| `/api/asr/transcribe-and-optimize` | ASR + 文本优化 | 语音记录 |
| `/api/asr/transcribe-and-translate` | ASR + 翻译 | 语音翻译 |
| `/api/llm/optimize` | 纯文本优化 | 文本后处理 |
| `/api/llm/translate` | 纯文本翻译 | 文本翻译 |

### 工具API

| 端点 | 功能 |
|------|------|
| `/api/status` | 服务状态检查 |
| `/api/health` | 健康检查 |
| `/api/hotwords` | 查看热词列表 |
| `/api/hotwords/reload` | 重新加载热词 |

---

## ⚡ 快速测试命令

### 流式优化API

```bash
# Python测试
python test_stream_api.py test.mp3

# curl测试
curl -X POST http://localhost:8000/api/asr/transcribe-and-optimize-stream \
  -F "audio=@test.mp3" \
  -F "use_vad=true" \
  -F "use_punc=true" \
  --no-buffer
```

### 流式翻译API

```bash
# Python测试（中文→英文）
python test_stream_translate_api.py test.mp3 中文 英文

# Python测试（英文→中文）
python test_stream_translate_api.py test.mp3 英文 中文

# curl测试
curl -X POST http://localhost:8000/api/asr/transcribe-and-translate-stream \
  -F "audio=@test.mp3" \
  -F "source_lang=中文" \
  -F "target_lang=英文" \
  --no-buffer
```

### 传统API测试

```bash
# ASR识别
curl -X POST http://localhost:8000/api/asr/transcribe \
  -F "audio=@test.mp3" | python3 -m json.tool

# ASR + 优化
curl -X POST http://localhost:8000/api/asr/transcribe-and-optimize \
  -F "audio=@test.mp3" | python3 -m json.tool

# ASR + 翻译
curl -X POST http://localhost:8000/api/asr/transcribe-and-translate \
  -F "audio=@test.mp3" \
  -F "source_lang=中文" \
  -F "target_lang=英文" | python3 -m json.tool
```

---

## 🔍 API选择指南

### 何时使用流式API？

✅ **推荐使用流式API：**
- 音频时长 > 3秒
- 需要显示处理进度
- 提升用户体验
- 实时反馈场景

❌ **不需要流式API：**
- 音频时长 < 3秒
- 批量处理任务
- 后台处理任务

### 功能选择

| 需求 | 推荐端点 |
|------|----------|
| 语音转文字 | `/api/asr/transcribe` |
| 语音转文字+优化 | `/api/asr/transcribe-and-optimize-stream` ⭐ |
| 语音翻译 | `/api/asr/transcribe-and-translate-stream` ⭐ |
| 文本优化 | `/api/llm/optimize` |
| 文本翻译 | `/api/llm/translate` |

---

## 📊 性能参考

| API类型 | ASR识别 | LLM处理 | 总时长 | 用户感知 |
|---------|---------|---------|--------|----------|
| 传统API | ~2秒 | ~3秒 | ~5秒 | 需等待5秒 |
| 流式API | ~2秒 | ~3秒 | ~5秒 | 2秒后可见ASR结果 ⭐ |

---

## 🔧 常用配置

### 热词设置

```bash
# 查看当前热词
curl http://localhost:8000/api/hotwords | python3 -m json.tool

# 重新加载热词
curl -X POST http://localhost:8000/api/hotwords/reload | python3 -m json.tool
```

### 服务状态

```bash
# 检查服务状态
curl http://localhost:8000/api/status | python3 -m json.tool

# 健康检查
curl http://localhost:8000/api/health

# 查看所有端点
curl http://localhost:8000/ | python3 -m json.tool
```

### 日志查看

```bash
# 查看实时日志
docker-compose logs -f ququ-backend

# 查看最近日志
docker-compose logs --tail 50 ququ-backend
```

---

## 🌐 API文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **完整文档**: `STREAMING_APIS_COMPLETE.md`
- **使用指南**: `STREAMING_API_GUIDE.md`

---

## 📝 请求示例

### Python示例

```python
import aiohttp
import asyncio

async def call_stream_api(audio_path):
    url = 'http://localhost:8000/api/asr/transcribe-and-translate-stream'

    with open(audio_path, 'rb') as f:
        audio_data = f.read()

    form_data = aiohttp.FormData()
    form_data.add_field('audio', audio_data, filename='audio.mp3')
    form_data.add_field('source_lang', '中文')
    form_data.add_field('target_lang', '英文')

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=form_data) as response:
            async for line in response.content:
                if line.startswith(b'data: '):
                    data = json.loads(line[6:])
                    print(f"[{data['stage']}] {data}")

asyncio.run(call_stream_api('test.mp3'))
```

### JavaScript示例

```javascript
async function callStreamAPI(audioFile) {
    const formData = new FormData();
    formData.append('audio', audioFile);
    formData.append('source_lang', '中文');
    formData.append('target_lang', '英文');

    const response = await fetch('http://localhost:8000/api/asr/transcribe-and-translate-stream', {
        method: 'POST',
        body: formData
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.substring(6));
                console.log(`[${data.stage}]`, data);
            }
        }
    }
}
```

---

## ✅ 部署检查清单

- [x] ✅ 流式优化API已实现
- [x] ✅ 流式翻译API已实现
- [x] ✅ 所有测试脚本已就绪
- [x] ✅ 完整文档已创建
- [x] ✅ 服务正常运行

**QuQu客户端可以立即开始集成！** 🚀

---

**最后更新**: 2025-10-16
