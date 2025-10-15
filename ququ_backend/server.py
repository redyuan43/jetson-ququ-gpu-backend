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


# ==================== API端点 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "QuQu Backend API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "asr": "/api/asr/transcribe",
            "llm": "/api/llm/optimize",
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
    hotword: str = Form("", description="热词")
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
        options = {
            "use_vad": use_vad,
            "use_punc": use_punc,
            "hotword": hotword
        }

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
        options = {
            "use_vad": use_vad,
            "use_punc": use_punc,
            "hotword": hotword
        }

        asr_result = funasr_server.transcribe_audio(str(temp_audio_path), options)

        if not asr_result["success"]:
            raise HTTPException(status_code=500, detail=asr_result.get("error", "转录失败"))

        recognized_text = asr_result["text"]

        # 2. 文本优化
        if optimize_mode != "none":
            llm_result = await ollama_client.optimize_text(
                text=recognized_text,
                mode=optimize_mode
            )

            if llm_result["success"]:
                optimized_text = llm_result["optimized_text"]
            else:
                logger.warning("文本优化失败，使用原始识别文本")
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


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "QuQu Backend is running"}


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
