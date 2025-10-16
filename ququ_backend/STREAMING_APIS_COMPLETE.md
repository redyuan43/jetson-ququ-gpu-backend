# 🌊 QuQu Backend 流式API完整文档

## 📋 概述

QuQu Backend 现在提供**完整的流式API支持**，包括文本优化和翻译功能。所有流式API均采用Server-Sent Events (SSE)格式，提供实时、分阶段的处理结果反馈。

---

## ✅ 可用的流式API端点

| 端点 | 功能 | 状态 |
|------|------|------|
| `/api/asr/transcribe-and-optimize-stream` | ASR识别 + LLM文本优化（流式）| ✅ 已实现 |
| `/api/asr/transcribe-and-translate-stream` | ASR识别 + 智能翻译（流式） | ✅ **新增** |

---

## 🎯 流式优化API

### 端点信息

- **URL**: `http://localhost:8000/api/asr/transcribe-and-optimize-stream`
- **方法**: `POST`
- **Content-Type**: `multipart/form-data`
- **响应格式**: `text/event-stream`

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `audio` | File | ✅ | - | 音频文件 |
| `use_vad` | Boolean | ❌ | true | 是否使用VAD |
| `use_punc` | Boolean | ❌ | true | 是否添加标点 |
| `hotword` | String | ❌ | "" | 自定义热词 |
| `optimize_mode` | String | ❌ | "optimize" | 优化模式 |

### 响应阶段

```
1. 🚀 start              - 开始处理
2. 🎤 asr_complete       - ASR识别完成 (包含识别文本)
3. ⚙️  optimizing         - 正在优化
4. ✨ optimize_complete  - 优化完成 (包含优化文本)
5. ✅ done               - 处理完成 (包含完整结果)
```

### 测试命令

```bash
# Python测试脚本
python test_stream_api.py <音频文件.mp3>

# curl测试
curl -X POST http://localhost:8000/api/asr/transcribe-and-optimize-stream \
  -F "audio=@test.mp3" \
  -F "use_vad=true" \
  -F "use_punc=true" \
  --no-buffer
```

---

## 🌍 流式翻译API

### 端点信息

- **URL**: `http://localhost:8000/api/asr/transcribe-and-translate-stream`
- **方法**: `POST`
- **Content-Type**: `multipart/form-data`
- **响应格式**: `text/event-stream`

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `audio` | File | ✅ | - | 音频文件 |
| `use_vad` | Boolean | ❌ | true | 是否使用VAD |
| `use_punc` | Boolean | ❌ | true | 是否添加标点 |
| `hotword` | String | ❌ | "" | 自定义热词 |
| `source_lang` | String | ❌ | "中文" | 源语言 |
| `target_lang` | String | ❌ | "英文" | 目标语言 |

### 响应阶段

```
1. 🚀 start               - 开始处理
2. 🎤 asr_complete        - ASR识别完成 (包含识别文本)
3. 🔄 translating         - 正在翻译
4. 🌍 translate_complete  - 翻译完成 (包含翻译文本)
5. ✅ done                - 处理完成 (包含完整结果)
```

### 测试命令

```bash
# Python测试脚本
python test_stream_translate_api.py <音频文件.mp3> 中文 英文

# curl测试
curl -X POST http://localhost:8000/api/asr/transcribe-and-translate-stream \
  -F "audio=@test.mp3" \
  -F "use_vad=true" \
  -F "use_punc=true" \
  -F "source_lang=中文" \
  -F "target_lang=英文" \
  --no-buffer
```

---

## 📊 完整API端点对比

### 流式API vs 传统API

| 功能 | 传统API端点 | 流式API端点 | 优势 |
|------|------------|-----------|------|
| ASR识别 | `/api/asr/transcribe` | ❌ 无需流式 | 已足够快 |
| ASR + 优化 | `/api/asr/transcribe-and-optimize` | `/api/asr/transcribe-and-optimize-stream` | ✅ 实时反馈 |
| ASR + 翻译 | `/api/asr/transcribe-and-translate` | `/api/asr/transcribe-and-translate-stream` | ✅ 实时反馈 |
| 纯文本优化 | `/api/llm/optimize` | ❌ 无需流式 | 处理快 |
| 纯文本翻译 | `/api/llm/translate` | ❌ 无需流式 | 处理快 |

### 性能对比

**流式优化API：**
- ASR识别：~2秒后可见
- LLM优化：~5秒完成
- 用户感知：实时进度 ✅

**流式翻译API：**
- ASR识别：~2秒后可见
- 智能翻译：~5-6秒完成
- 用户感知：实时进度 ✅

**传统API：**
- 处理时长：~5-6秒
- 用户感知：需等待完成 ❌

---

## 💻 客户端集成示例

### JavaScript/Fetch API示例

```javascript
async function transcribeAndTranslate(audioFile, sourceLang = '中文', targetLang = '英文') {
    const formData = new FormData();
    formData.append('audio', audioFile);
    formData.append('use_vad', 'true');
    formData.append('use_punc', 'true');
    formData.append('source_lang', sourceLang);
    formData.append('target_lang', targetLang);

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

                switch (data.stage) {
                    case 'start':
                        showProgress('处理中...');
                        break;
                    case 'asr_complete':
                        updateASRText(data.text);
                        break;
                    case 'translating':
                        showProgress('正在翻译...');
                        break;
                    case 'translate_complete':
                        updateTranslatedText(data.text);
                        break;
                    case 'done':
                        hideProgress();
                        showFinalResult(data.asr_text, data.translated_text);
                        break;
                    case 'error':
                        showError(data.error);
                        break;
                }
            }
        }
    }
}
```

### Python/aiohttp示例

```python
import aiohttp
import asyncio
import json

async def transcribe_and_translate_stream(audio_path, source_lang='中文', target_lang='英文'):
    url = 'http://localhost:8000/api/asr/transcribe-and-translate-stream'

    with open(audio_path, 'rb') as f:
        audio_data = f.read()

    form_data = aiohttp.FormData()
    form_data.add_field('audio', audio_data, filename='audio.mp3')
    form_data.add_field('use_vad', 'true')
    form_data.add_field('use_punc', 'true')
    form_data.add_field('source_lang', source_lang)
    form_data.add_field('target_lang', target_lang)

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=form_data) as response:
            async for line in response.content:
                line = line.decode('utf-8').strip()

                if line.startswith('data: '):
                    data = json.loads(line[6:])

                    if data['stage'] == 'asr_complete':
                        print(f"识别: {data['text']}")
                    elif data['stage'] == 'translate_complete':
                        print(f"翻译: {data['text']}")
                    elif data['stage'] == 'done':
                        print(f"完成!")
                        print(f"原文: {data['asr_text']}")
                        print(f"译文: {data['translated_text']}")
```

---

## 🧪 测试工具

### 可用的测试脚本

1. **流式优化API测试**：
   ```bash
   python test_stream_api.py <音频文件>
   ```

2. **流式翻译API测试**：
   ```bash
   python test_stream_translate_api.py <音频文件> [源语言] [目标语言]
   ```

3. **HTML可视化测试**：
   ```bash
   xdg-open test_stream_client.html
   ```

### 测试输出示例

```
📤 上传音频: test.mp3
🌐 连接到: http://localhost:8000/api/asr/transcribe-and-translate-stream
🔄 翻译方向: 中文 → 英文
------------------------------------------------------------
✅ 连接成功，开始接收流式数据...

🚀 [start] 开始处理音频

🎤 [asr_complete] ASR识别完成:
   文本: 我想使用Qwen和Docker
   时长: 2.50秒

🔄 [translating] 正在翻译 (中文 → 英文)

🌍 [translate_complete] 翻译完成:
   译文: I want to use Qwen and Docker

✅ [done] 处理完成

============================================================
📊 最终结果:
   原文 (中文): 我想使用Qwen和Docker
   译文 (英文): I want to use Qwen and Docker
============================================================
```

---

## 🔍 响应数据格式详解

### 优化API响应格式

**阶段1 - start:**
```json
{
  "stage": "start",
  "message": "开始处理音频",
  "timestamp": 12345.678
}
```

**阶段2 - asr_complete:**
```json
{
  "stage": "asr_complete",
  "text": "识别的文本内容",
  "duration": 2.5,
  "timestamp": 12347.890
}
```

**阶段3 - optimizing:**
```json
{
  "stage": "optimizing",
  "message": "正在优化文本"
}
```

**阶段4 - optimize_complete:**
```json
{
  "stage": "optimize_complete",
  "text": "优化后的文本",
  "timestamp": 12350.123
}
```

**阶段5 - done:**
```json
{
  "stage": "done",
  "message": "处理完成",
  "asr_text": "ASR识别的文本",
  "optimized_text": "LLM优化后的文本",
  "timestamp": 12350.124
}
```

### 翻译API响应格式

**阶段1 - start:**
```json
{
  "stage": "start",
  "message": "开始处理音频",
  "timestamp": 12345.678
}
```

**阶段2 - asr_complete:**
```json
{
  "stage": "asr_complete",
  "text": "识别的中文文本",
  "duration": 2.5,
  "timestamp": 12347.890
}
```

**阶段3 - translating:**
```json
{
  "stage": "translating",
  "message": "正在翻译 (中文 → 英文)"
}
```

**阶段4 - translate_complete:**
```json
{
  "stage": "translate_complete",
  "text": "Translated English text",
  "timestamp": 12353.456
}
```

**阶段5 - done:**
```json
{
  "stage": "done",
  "message": "处理完成",
  "asr_text": "识别的中文文本",
  "translated_text": "Translated English text",
  "source_lang": "中文",
  "target_lang": "英文",
  "timestamp": 12353.457
}
```

**错误响应:**
```json
{
  "stage": "error",
  "error": "错误信息描述"
}
```

---

## ⚙️ 高级配置

### 支持的语言对

| 源语言 | 目标语言 | 状态 |
|--------|---------|------|
| 中文 | 英文 | ✅ 支持 |
| 英文 | 中文 | ✅ 支持 |
| 其他 | 其他 | ✅ LLM支持多种语言 |

### 热词配置

流式API自动加载 `hotwords.txt` 中的系统热词，也可以在请求中指定额外的热词：

```bash
curl -X POST http://localhost:8000/api/asr/transcribe-and-translate-stream \
  -F "audio=@test.mp3" \
  -F "hotword=Qwen Docker GitHub" \  # 额外热词
  --no-buffer
```

### 性能调优

**优化建议：**
1. 使用VAD可以提高长音频处理速度
2. 热词数量建议控制在50个以内
3. 流式API适合3秒以上的音频
4. 短音频（<3秒）可以使用传统API

---

## 🐛 故障排查

### 问题1：收不到流式数据

**检查**：
```bash
# 测试连接
curl http://localhost:8000/api/health

# 查看日志
docker-compose logs -f ququ-backend
```

### 问题2：翻译结果不正确

**原因**：
- LLM模型配置问题
- 提示词需要优化

**解决**：
```bash
# 检查Ollama状态
curl http://localhost:11434/v1/models

# 查看当前使用的模型
curl http://localhost:8000/api/status | python3 -m json.tool
```

### 问题3：流式数据被缓冲

**原因**：nginx或代理服务器缓冲了响应

**解决**：
- 响应头已包含 `X-Accel-Buffering: no`
- 在nginx配置中添加 `proxy_buffering off;`

---

## 📚 相关文档

- **完整使用指南**: `STREAMING_API_GUIDE.md`
- **部署报告**: `STREAM_API_DEPLOYMENT_REPORT.md`
- **QuQu Backend README**: `README.md`
- **API文档**: http://localhost:8000/docs

---

## 🎉 总结

### ✅ 已实现功能

| 功能 | 状态 |
|------|------|
| 流式ASR识别 + 文本优化 | ✅ 完成 |
| 流式ASR识别 + 智能翻译 | ✅ **新增** |
| Python测试脚本 | ✅ 完成 |
| HTML测试页面 | ✅ 完成 |
| 完整文档 | ✅ 完成 |

### 🚀 QuQu客户端集成准备

**所有流式API已就绪！**

QuQu客户端现在可以：
1. 使用流式优化API获取实时ASR和优化结果
2. 使用流式翻译API获取实时ASR和翻译结果
3. 显示处理进度，提升用户体验

**推荐使用场景：**
- ✅ 语音记录 + 实时转文字 → 使用优化API
- ✅ 语音输入 + 实时翻译 → 使用翻译API
- ✅ 所有场景都能实时显示处理进度

---

**最后更新**: 2025-10-16
**版本**: v1.1.0 (新增流式翻译API)
