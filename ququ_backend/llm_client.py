#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama LLM客户端
用于文本优化和处理
"""

import os
import logging
import httpx
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class OllamaClient:
    """Ollama API客户端"""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        """
        初始化Ollama客户端

        Args:
            base_url: Ollama API地址，默认为环境变量OLLAMA_BASE_URL或localhost:11434
            model: 使用的模型名称，默认为gpt-oss:20b
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        # 确保URL格式正确
        if not self.base_url.endswith("/v1"):
            if self.base_url.endswith("/"):
                self.base_url = self.base_url + "v1"
            else:
                self.base_url = self.base_url + "/v1"

        self.model = model or os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
        self.timeout = 60.0
        logger.info(f"初始化Ollama客户端: {self.base_url}, 模型: {self.model}")

    async def optimize_text(self, text: str, mode: str = "optimize", custom_prompt: Optional[str] = None,
                           hotwords_context: Optional[str] = None) -> Dict[str, Any]:
        """
        使用LLM优化文本

        Args:
            text: 原始文本
            mode: 优化模式 (optimize/format/custom)
            custom_prompt: 自定义提示词

        Returns:
            包含优化结果的字典
        """
        try:
            prompt = self._build_prompt(text, mode, custom_prompt, hotwords_context)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "你是一个语言理解大师，非常会理解用户的语言表达。并且能够很好的总结和优化文本。"},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "stream": False,
                        "think": False,
                        "options": {
                            "num_predict": 512
                        }
                    }
                )

                if response.status_code != 200:
                    logger.error(f"Ollama API错误: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API请求失败: {response.status_code}",
                        "original_text": text
                    }

                result = response.json()
                optimized_text = result["choices"][0]["message"]["content"].strip()

                logger.info(f"文本优化成功，原文长度: {len(text)}, 优化后长度: {len(optimized_text)}")

                return {
                    "success": True,
                    "original_text": text,
                    "optimized_text": optimized_text,
                    "mode": mode,
                    "model": self.model
                }

        except httpx.TimeoutException:
            logger.error("Ollama API请求超时")
            return {
                "success": False,
                "error": "请求超时",
                "original_text": text
            }
        except Exception as e:
            logger.error(f"文本优化失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "original_text": text
            }

    def _build_prompt(self, text: str, mode: str, custom_prompt: Optional[str] = None,
                      hotwords_context: Optional[str] = None) -> str:
        """构建优化提示词"""
        if custom_prompt:
            return f"{custom_prompt}\n\n原文：\n{text}"

        # 准备热词对照表
        hotwords_section = ""
        if hotwords_context:
            hotwords_section = f"{hotwords_context}"

        prompts = {
            "optimize": f"""纠正语音识别错误，理解用户真实意图。

用户是科技工作者，经常谈论AI模型、技术工具、社交平台等专有名词，但语音识别常出错。

任务：
1. 理解句子整体含义和主题（谈AI模型？谈社交媒体？）
2. 找出拼写奇怪、发音相似的词，结合上下文判断应该是哪个专有名词
3. 纠正专有名词，删除口头语（嗯、啊、那个等）
4. 保持句子原意和结构

原文：{text}

直接输出纠正后的文本：""",

            "format": f"""请将以下文本格式化为正式的书面语：
1. 保持原意不变
2. 使用恰当的标点符号
3. 分段组织内容
4. 使用规范的书面语表达

原文：
{text}

请直接输出格式化后的文本。""",

            "punctuate": f"""请为以下文本添加合适的标点符号，使其更易读：

原文：
{text}

请直接输出添加标点后的文本。"""
        }

        return prompts.get(mode, prompts["optimize"])

    async def check_health(self) -> Dict[str, Any]:
        """检查Ollama服务健康状态"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/models")

                if response.status_code == 200:
                    models = response.json()
                    return {
                        "success": True,
                        "available": True,
                        "base_url": self.base_url,
                        "model": self.model,
                        "models": models.get("data", [])
                    }
                else:
                    return {
                        "success": False,
                        "available": False,
                        "error": f"HTTP {response.status_code}"
                    }

        except Exception as e:
            logger.error(f"Ollama健康检查失败: {str(e)}")
            return {
                "success": False,
                "available": False,
                "error": str(e)
            }
