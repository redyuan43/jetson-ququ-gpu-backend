#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuQu Backend Server
基于FastAPI的GPU加速FunASR语音识别服务
"""

import os
import sys
import logging
import tempfile
import asyncio
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 导入自定义模块
from funasr_gpu import FunASRServer
from llm_client import OllamaClient
from hotwords_with_variants import format_hotwords_for_llm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/tmp/ququ_backend.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# 全局变量
funasr_server: Optional[FunASRServer] = None
ollama_client: Optional[OllamaClient] = None

# 热词缓存
_hotwords_cache: Optional[str] = None
_hotwords_file_mtime: float = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global funasr_server, ollama_client

    # 启动时初始化
    logger.info("🚀 启动QuQu Backend Server...")

    # 初始化FunASR
    logger.info("初始化FunASR GPU服务...")
    funasr_server = FunASRServer()
    init_result = funasr_server.initialize()

    if init_result["success"]:
        logger.info(f"✅ FunASR初始化成功: {init_result['message']}")
    else:
        logger.error(f"❌ FunASR初始化失败: {init_result.get('error')}")
        # 不阻塞启动，允许后续再次初始化

    # 初始化Ollama客户端
    logger.info("初始化Ollama客户端...")
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://192.168.100.38:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
    ollama_client = OllamaClient(base_url=ollama_base_url, model=ollama_model)

    # 检查Ollama健康状态
    health = await ollama_client.check_health()
    if health["success"]:
        logger.info(f"✅ Ollama服务可用: {ollama_base_url}")
    else:
        logger.warning(f"⚠️ Ollama服务不可用: {health.get('error')}")

    logger.info("✨ QuQu Backend Server启动完成")

    yield

    # 关闭时清理
    logger.info("🛑 关闭QuQu Backend Server...")


# 创建FastAPI应用
app = FastAPI(
    title="QuQu Backend API",
    description="GPU加速的FunASR语音识别服务 + Ollama文本优化",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 辅助函数 ====================

def load_hotwords() -> str:
    """
    加载热词文件
    自动检测文件更新并重新加载
    Returns:
        str: 空格分隔的热词字符串
    """
    global _hotwords_cache, _hotwords_file_mtime

    hotwords_file = Path(__file__).parent / "hotwords.txt"

    if not hotwords_file.exists():
        logger.warning(f"热词文件不存在: {hotwords_file}")
        return ""

    try:
        # 检查文件是否更新
        current_mtime = hotwords_file.stat().st_mtime

        if _hotwords_cache is None or current_mtime > _hotwords_file_mtime:
            # 读取热词文件
            with open(hotwords_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 过滤注释和空行，提取热词
            hotwords = []
            for line in lines:
                line = line.strip()
                # 跳过空行和注释
                if line and not line.startswith('#'):
                    hotwords.append(line)

            # 用空格连接所有热词
            _hotwords_cache = ' '.join(hotwords)
            _hotwords_file_mtime = current_mtime

            logger.info(f"热词已加载: {len(hotwords)}个词")
            logger.debug(f"热词内容: {_hotwords_cache[:200]}...")

        return _hotwords_cache

    except Exception as e:
        logger.error(f"加载热词文件失败: {str(e)}")
        return ""


def merge_hotwords(user_hotwords: str = "") -> str:
    """
    合并用户提供的热词和系统热词
    Args:
        user_hotwords: 用户提供的热词（空格分隔）
    Returns:
        str: 合并后的热词字符串
    """
    system_hotwords = load_hotwords()

    if user_hotwords:
        # 合并用户热词和系统热词
        all_hotwords = f"{system_hotwords} {user_hotwords}".strip()
    else:
        all_hotwords = system_hotwords

    return all_hotwords


# ==================== 数据模型 ====================

class TranscriptionOptions(BaseModel):
    """转录选项"""
    use_vad: bool = True
    use_punc: bool = True
    hotword: str = ""


class OptimizeRequest(BaseModel):
    """文本优化请求"""
    text: str
    mode: str = "optimize"  # optimize/format/custom
    custom_prompt: Optional[str] = None


class TranslateRequest(BaseModel):
    """文本翻译请求"""
    text: str
    source_lang: str = "中文"
    target_lang: str = "英文"


# ==================== API端点 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "QuQu Backend API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "asr_transcribe": "/api/asr/transcribe",
            "asr_transcribe_and_optimize": "/api/asr/transcribe-and-optimize",
            "asr_transcribe_and_translate": "/api/asr/transcribe-and-translate",
            "llm_optimize": "/api/llm/optimize",
            "llm_translate": "/api/llm/translate",
            "status": "/api/status",
            "docs": "/docs"
        }
    }


@app.get("/api/status")
async def get_status():
    """获取服务状态"""
    global funasr_server, ollama_client

    # 检查FunASR状态
    funasr_status = {}
    if funasr_server:
        funasr_status = funasr_server.check_status()
    else:
        funasr_status = {"success": False, "error": "FunASR未初始化"}

    # 检查Ollama状态
    ollama_status = {}
    if ollama_client:
        ollama_status = await ollama_client.check_health()
    else:
        ollama_status = {"success": False, "error": "Ollama客户端未初始化"}

    # 获取GPU状态
    gpu_available = False
    try:
        import torch
        gpu_available = torch.cuda.is_available()
    except:
        pass

    return {
        "success": True,
        "funasr": funasr_status,
        "ollama": ollama_status,
        "gpu_available": gpu_available,
        "performance_stats": funasr_server.get_performance_stats() if funasr_server else {}
    }


@app.post("/api/asr/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(..., description="音频文件"),
    use_vad: bool = Form(True, description="是否使用VAD"),
    use_punc: bool = Form(True, description="是否添加标点"),
    hotword: str = Form("", description="热词（空格分隔，自动加载hotwords.txt）")
):
    """
    语音识别接口

    Args:
        audio: 音频文件（支持wav, mp3, m4a等格式）
        use_vad: 是否使用VAD（语音活动检测）
        use_punc: 是否添加标点符号
        hotword: 热词，用空格分隔

    Returns:
        识别结果
    """
    global funasr_server

    if not funasr_server or not funasr_server.initialized:
        raise HTTPException(status_code=503, detail="FunASR服务未就绪，请稍后重试")

    # 保存临时音频文件
    temp_dir = tempfile.mkdtemp()
    temp_audio_path = Path(temp_dir) / audio.filename

    try:
        # 写入音频文件
        content = await audio.read()
        with open(temp_audio_path, "wb") as f:
            f.write(content)

        logger.info(f"收到转录请求: {audio.filename}, 大小: {len(content)} bytes")

        # 执行转录
        # 合并系统热词和用户热词
        merged_hotwords = merge_hotwords(hotword)

        options = {
            "use_vad": use_vad,
            "use_punc": use_punc,
            "hotword": merged_hotwords
        }

        logger.info(f"使用热词数: {len(merged_hotwords.split()) if merged_hotwords else 0}")

        result = funasr_server.transcribe_audio(str(temp_audio_path), options)

        if result["success"]:
            logger.info(f"转录成功: {result['text'][:100]}...")
            return JSONResponse(content=result)
        else:
            logger.error(f"转录失败: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get("error", "转录失败"))

    except Exception as e:
        logger.error(f"转录请求处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # 清理临时文件
        try:
            temp_audio_path.unlink()
            Path(temp_dir).rmdir()
        except:
            pass


@app.post("/api/llm/optimize")
async def optimize_text(request: OptimizeRequest):
    """
    文本优化接口

    Args:
        request: 包含text, mode, custom_prompt的请求

    Returns:
        优化后的文本
    """
    global ollama_client

    if not ollama_client:
        raise HTTPException(status_code=503, detail="Ollama客户端未初始化")

    logger.info(f"收到文本优化请求: 模式={request.mode}, 长度={len(request.text)}")

    result = await ollama_client.optimize_text(
        text=request.text,
        mode=request.mode,
        custom_prompt=request.custom_prompt
    )

    if result["success"]:
        logger.info("文本优化成功")
        return JSONResponse(content=result)
    else:
        logger.error(f"文本优化失败: {result.get('error')}")
        raise HTTPException(status_code=500, detail=result.get("error", "文本优化失败"))


@app.post("/api/llm/translate")
async def translate_text(request: TranslateRequest):
    """
    文本翻译接口

    Args:
        request: 包含text, source_lang, target_lang的请求

    Returns:
        翻译后的文本

    示例:
        POST /api/llm/translate
        {
            "text": "你好世界",
            "source_lang": "中文",
            "target_lang": "英文"
        }
    """
    global ollama_client

    if not ollama_client:
        raise HTTPException(status_code=503, detail="Ollama客户端未初始化")

    logger.info(f"收到翻译请求: {request.source_lang} -> {request.target_lang}, 长度={len(request.text)}")

    result = await ollama_client.translate_text(
        text=request.text,
        source_lang=request.source_lang,
        target_lang=request.target_lang
    )

    if result["success"]:
        logger.info(f"翻译成功: {request.source_lang} -> {request.target_lang}")
        return JSONResponse(content=result)
    else:
        logger.error(f"翻译失败: {result.get('error')}")
        raise HTTPException(status_code=500, detail=result.get("error", "翻译失败"))


@app.post("/api/asr/transcribe-and-optimize")
async def transcribe_and_optimize(
    audio: UploadFile = File(..., description="音频文件"),
    use_vad: bool = Form(True),
    use_punc: bool = Form(True),
    hotword: str = Form(""),
    optimize_mode: str = Form("optimize", description="优化模式")
):
    """
    一体化接口：语音识别 + 文本优化

    Args:
        audio: 音频文件
        use_vad: 是否使用VAD
        use_punc: 是否添加标点
        hotword: 热词
        optimize_mode: 优化模式

    Returns:
        识别和优化后的结果
    """
    global funasr_server, ollama_client

    if not funasr_server or not funasr_server.initialized:
        raise HTTPException(status_code=503, detail="FunASR服务未就绪")

    if not ollama_client:
        raise HTTPException(status_code=503, detail="Ollama客户端未初始化")

    # 保存临时音频文件
    temp_dir = tempfile.mkdtemp()
    temp_audio_path = Path(temp_dir) / audio.filename

    try:
        # 写入音频文件
        content = await audio.read()
        with open(temp_audio_path, "wb") as f:
            f.write(content)

        logger.info(f"收到一体化请求: {audio.filename}")

        # 1. 语音识别
        # 合并系统热词和用户热词
        merged_hotwords = merge_hotwords(hotword)

        options = {
            "use_vad": use_vad,
            "use_punc": use_punc,
            "hotword": merged_hotwords
        }

        logger.info(f"一体化处理 - 使用热词数: {len(merged_hotwords.split()) if merged_hotwords else 0}")

        asr_result = funasr_server.transcribe_audio(str(temp_audio_path), options)

        if not asr_result["success"]:
            raise HTTPException(status_code=500, detail=asr_result.get("error", "转录失败"))

        recognized_text = asr_result["text"]

        # 2. 文本优化
        if optimize_mode != "none":
            # 格式化热词为LLM易读的格式（包含常见误识别变体）
            hotwords_list = merged_hotwords.split() if merged_hotwords else []
            hotwords_formatted = format_hotwords_for_llm(hotwords_list, max_words=50)

            llm_result = await ollama_client.optimize_text(
                text=recognized_text,
                mode=optimize_mode,
                hotwords_context=hotwords_formatted if hotwords_formatted else None
            )

            # 简单决策：LLM成功就用LLM结果，失败就用ASR原文
            if llm_result["success"]:
                optimized_text = llm_result["optimized_text"]
                logger.info(f"文本优化成功，原文长度: {len(recognized_text)}, 优化后长度: {len(optimized_text)}")
            else:
                logger.warning(f"文本优化失败，使用原始识别文本: {llm_result.get('error')}")
                optimized_text = recognized_text
        else:
            optimized_text = recognized_text

        return JSONResponse(content={
            "success": True,
            "asr_result": asr_result,
            "recognized_text": recognized_text,
            "optimized_text": optimized_text,
            "optimize_mode": optimize_mode
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"一体化请求处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # 清理临时文件
        try:
            temp_audio_path.unlink()
            Path(temp_dir).rmdir()
        except:
            pass


@app.post("/api/asr/transcribe-and-translate")
async def transcribe_and_translate(
    audio: UploadFile = File(..., description="音频文件"),
    use_vad: bool = Form(True),
    use_punc: bool = Form(True),
    hotword: str = Form(""),
    source_lang: str = Form("中文", description="源语言"),
    target_lang: str = Form("英文", description="目标语言")
):
    """
    一体化接口：语音识别 + 智能翻译（优化版）

    处理流程（性能优化，2步完成）：
    1. FunASR语音识别 → 中文文本
    2. LLM智能翻译 → 理解真实意图 + 纠正专有名词 + 翻译成英文（一步完成）

    性能对比：
    - 旧版：ASR(~2s) + 优化(~3s) + 翻译(~3s) = ~8秒
    - 新版：ASR(~2s) + 智能翻译(~3-4s) = ~5-6秒 ⚡

    Args:
        audio: 音频文件
        use_vad: 是否使用VAD
        use_punc: 是否添加标点
        hotword: 热词
        source_lang: 源语言（默认：中文）
        target_lang: 目标语言（默认：英文）

    Returns:
        识别和智能翻译后的结果
    """
    global funasr_server, ollama_client

    if not funasr_server or not funasr_server.initialized:
        raise HTTPException(status_code=503, detail="FunASR服务未就绪")

    if not ollama_client:
        raise HTTPException(status_code=503, detail="Ollama客户端未初始化")

    # 保存临时音频文件
    temp_dir = tempfile.mkdtemp()
    temp_audio_path = Path(temp_dir) / audio.filename

    try:
        # 写入音频文件
        content = await audio.read()
        with open(temp_audio_path, "wb") as f:
            f.write(content)

        logger.info(f"收到语音翻译请求: {audio.filename}, {source_lang} -> {target_lang}")

        # 1. 语音识别
        merged_hotwords = merge_hotwords(hotword)
        options = {
            "use_vad": use_vad,
            "use_punc": use_punc,
            "hotword": merged_hotwords
        }

        asr_result = funasr_server.transcribe_audio(str(temp_audio_path), options)

        if not asr_result["success"]:
            raise HTTPException(status_code=500, detail=asr_result.get("error", "转录失败"))

        recognized_text = asr_result["text"]
        logger.info(f"识别成功: {recognized_text[:100]}...")

        # 2. ASR智能翻译（优化+翻译一步完成，提升速度）
        translate_result = await ollama_client.translate_from_asr(
            text=recognized_text,
            source_lang=source_lang,
            target_lang=target_lang
        )

        if translate_result["success"]:
            translated_text = translate_result["translated_text"]
            logger.info(f"ASR智能翻译成功: {source_lang} -> {target_lang}")
        else:
            logger.warning(f"翻译失败，返回原文: {translate_result.get('error')}")
            translated_text = recognized_text

        return JSONResponse(content={
            "success": True,
            "asr_result": asr_result,
            "recognized_text": recognized_text,
            "translated_text": translated_text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "mode": "asr_smart_translate"  # 标识使用了智能翻译模式
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"语音翻译请求处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # 清理临时文件
        try:
            temp_audio_path.unlink()
            Path(temp_dir).rmdir()
        except:
            pass


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "QuQu Backend is running"}


@app.get("/api/hotwords")
async def get_hotwords():
    """
    获取当前加载的热词列表

    Returns:
        热词信息
    """
    hotwords_str = load_hotwords()
    hotwords_list = hotwords_str.split() if hotwords_str else []

    return {
        "success": True,
        "count": len(hotwords_list),
        "hotwords": hotwords_list,
        "hotwords_string": hotwords_str
    }


@app.post("/api/hotwords/reload")
async def reload_hotwords():
    """
    重新加载热词文件

    Returns:
        重新加载结果
    """
    global _hotwords_cache, _hotwords_file_mtime

    # 清空缓存强制重新加载
    _hotwords_cache = None
    _hotwords_file_mtime = 0

    hotwords_str = load_hotwords()
    hotwords_list = hotwords_str.split() if hotwords_str else []

    return {
        "success": True,
        "message": "热词已重新加载",
        "count": len(hotwords_list),
        "hotwords": hotwords_list[:20]  # 只返回前20个作为预览
    }


# ==================== 主程序 ====================

if __name__ == "__main__":
    # 获取配置
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    workers = int(os.getenv("SERVER_WORKERS", "1"))

    logger.info(f"启动服务器: {host}:{port}, workers={workers}")

    # 启动服务器
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        access_log=True
    )
