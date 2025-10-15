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

    async def optimize_text(self, text: str, mode: str = "optimize", custom_prompt: Optional[str] = None) -> Dict[str, Any]:
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
            prompt = self._build_prompt(text, mode, custom_prompt)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "你是一个专业的文本编辑助手，擅长优化和润色中文文本。"},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "stream": False
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

    def _build_prompt(self, text: str, mode: str, custom_prompt: Optional[str] = None) -> str:
        """构建优化提示词"""
        if custom_prompt:
            return f"{custom_prompt}\n\n原文：\n{text}"

        prompts = {
            "optimize": f"""请优化以下语音识别文本，完成这些任务：
1. 删除口头禅和无意义的词语（如"嗯"、"啊"、"那个"等）
2. 修正明显的口误和语法错误
3. 保持原意不变，使表达更流畅自然
4. 如果有明显的自我纠正（如"周三开会，不对，是周四"），只保留正确的部分

原文：
{text}

请直接输出优化后的文本，不要添加任何说明或注释。""",

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
