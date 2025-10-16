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
            hotwords_section = f"""

【⚠️ 专有名词对照表 - 必须严格遵循】
以下是确定的误识别→正确形式映射，请优先使用：
{hotwords_context}
"""

        prompts = {
            "optimize": f"""你的任务：纠正语音识别中的专有名词错误。

【重要规则】
1. **优先查对照表**：如果原文的词在"专有名词对照表"中，必须替换为对照表的正确形式
2. **不要过度推断**：只纠正明确错误的专有名词，不要改变其他内容
3. **删除口头语**：去掉"嗯"、"啊"、"那个"等语气词
4. **保持原意**：不改变人称、语气和句式

【常见专有名词参考】
AI模型: Gemma, Qwen, Qwen3, Qwen2.5, DeepSeek, ChatGPT, GPT, Claude, LLaMA
技术工具: PyTorch, TensorFlow, CUDA, Ollama, Docker, Hugging Face, Home Assistant
社交平台: Facebook, Reddit, Twitter, YouTube, GitHub, LinkedIn
{hotwords_section}
【示例】
原文："我想使用千万二点五和deep sik大模型"
纠正："我想使用Qwen2.5和DeepSeek大模型"

原文：{text}

请直接输出纠正后的文本，不要包含任何前缀或格式标记。""",

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

    async def translate_from_asr(self, text: str, source_lang: str = "中文", target_lang: str = "英文") -> Dict[str, Any]:
        """
        针对ASR识别结果的智能翻译（优化+翻译一步完成）

        Args:
            text: ASR识别的原始文本
            source_lang: 源语言（默认：中文）
            target_lang: 目标语言（默认：英文）

        Returns:
            包含翻译结果的字典
        """
        try:
            prompt = f"""你的任务：理解语音识别结果的真实意图，并翻译成{target_lang}。

【重要背景】
这段文本是语音识别的结果，可能包含错误：
- 专有名词识别错误（如："deep sik" → "DeepSeek", "乾文二点五" → "Qwen2.5"）
- 口头语和语气词（嗯、啊、那个等）
- 发音相似导致的误识别

【常见专有名词参考】
AI模型: Gemma, Qwen, Qwen3, Qwen2.5, DeepSeek, ChatGPT, GPT, Claude, LLaMA
技术工具: PyTorch, TensorFlow, CUDA, Ollama, Docker, Hugging Face
社交平台: Facebook, Reddit, Twitter, YouTube, GitHub, LinkedIn

【任务步骤】
1. 理解句子真实含义和主题
2. 识别并纠正专有名词的误识别
3. 删除口头语和语气词
4. 翻译成准确、地道的{target_lang}

【要求】
- 专有名词必须使用正确的英文形式
- 保持原文的语气和风格
- 使用地道的{target_lang}表达
- 直接输出翻译结果，不要解释

【原文】
{text}

【{target_lang}翻译】"""

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": f"你是一个专业的翻译助手，擅长理解语音识别结果并准确翻译。特别擅长处理技术类专有名词。"},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "stream": False,
                        "think": False,
                        "options": {
                            "num_predict": 1024
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
                translated_text = result["choices"][0]["message"]["content"].strip()

                logger.info(f"ASR智能翻译成功: {source_lang} -> {target_lang}, 原文长度: {len(text)}, 译文长度: {len(translated_text)}")

                return {
                    "success": True,
                    "original_text": text,
                    "translated_text": translated_text,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "model": self.model,
                    "mode": "asr_translate"  # 标识这是ASR直接翻译模式
                }

        except httpx.TimeoutException:
            logger.error("Ollama API请求超时")
            return {
                "success": False,
                "error": "请求超时",
                "original_text": text
            }
        except Exception as e:
            logger.error(f"ASR智能翻译失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "original_text": text
            }

    async def translate_text(self, text: str, source_lang: str = "中文", target_lang: str = "英文") -> Dict[str, Any]:
        """
        翻译文本

        Args:
            text: 原始文本
            source_lang: 源语言（默认：中文）
            target_lang: 目标语言（默认：英文）

        Returns:
            包含翻译结果的字典
        """
        try:
            prompt = f"""请将以下{source_lang}翻译成{target_lang}。

要求：
1. 准确翻译原文意思
2. 保持原文的语气和风格
3. 使用地道的{target_lang}表达
4. 直接输出翻译结果，不要添加任何解释

原文：{text}

翻译："""

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": f"你是一个专业的翻译助手，擅长{source_lang}到{target_lang}的翻译。"},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,  # 翻译使用较低temperature保证准确性
                        "stream": False,
                        "think": False,
                        "options": {
                            "num_predict": 1024
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
                translated_text = result["choices"][0]["message"]["content"].strip()

                logger.info(f"翻译成功: {source_lang} -> {target_lang}, 原文长度: {len(text)}, 译文长度: {len(translated_text)}")

                return {
                    "success": True,
                    "original_text": text,
                    "translated_text": translated_text,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
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
            logger.error(f"翻译失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "original_text": text
            }

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
