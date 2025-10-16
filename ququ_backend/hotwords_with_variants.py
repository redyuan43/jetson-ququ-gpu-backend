#!/usr/bin/env python3
"""
热词及其常见误识别变体映射表
帮助LLM更准确地识别和纠正专有名词
"""

# 专有名词及其常见误识别形式
# 格式：正确形式 -> [常见误识别形式列表]
HOTWORD_VARIANTS = {
    # AI模型 - 谷歌
    "Gemma": ["jam", "jmine", "jammy", "兼摆", "面来", "gem", "jemma"],
    "Google Gemma": ["google的jam", "google jmine", "谷歌jam"],

    # AI模型 - 阿里（优先使用英文原名）
    "Qwen3": ["千win三", "千问三", "切问三", "千文三", "qwen3", "千问3"],
    "Qwen": ["千win", "千问", "切问", "千文"],
    "Qwen2.5": ["千win2.5", "千问2.5", "切问2.5", "千问2点5", "千万二点五", "千万2.5", "切万二点五", "切万2.5", "切win2.5"],

    # AI模型 - DeepSeek
    "DeepSeek": ["deep seek", "deep sic", "deep sick", "deep sik", "depsic", "depsik", "深度寻求", "deepseek", "蒂普西克"],

    # AI模型 - OpenAI
    "ChatGPT": ["chat gpt", "chat机批踢", "洽特机批踢"],
    "GPT": ["机批踢", "g p t"],
    "GPT-4": ["机批踢4", "gpt4", "g p t 4"],

    # AI模型 - Anthropic
    "Claude": ["克劳德", "claude", "克洛德"],

    # AI模型 - Meta
    "LLaMA": ["拉马", "llama", "羊驼"],
    "Llama": ["拉马", "llama", "羊驼"],

    # 互联网平台
    "Reddit": ["redit", "i adit", "red第特", "reditt", "reddiit", "瑞迪特"],
    "Facebook": ["facebook", "脸书", "飞死book", "facbook"],
    "X.com": ["x点com", "x.com", "x dot com", "x com"],
    "Twitter": ["推特", "twitter", "twiter"],
    "YouTube": ["youtube", "油管", "you tube", "优兔"],
    "GitHub": ["github", "git hub", "吉特哈布"],
    "LinkedIn": ["linkedin", "领英", "linked in"],

    # 技术框架
    "PyTorch": ["拍吐气", "派吐气", "pytorch", "py torch", "拍托吃"],
    "TensorFlow": ["tensor flow", "tens流", "坦瑟福楼"],
    "CUDA": ["库达", "cuda", "酷大"],

    # 硬件
    "Jetson": ["杰森", "jetson", "捷森"],
    "AGX Orin": ["agx orin", "欧林", "奥林"],

    # 工具
    "Ollama": ["欧拉马", "ollama", "o拉马"],
    "Docker": ["多克", "docker", "道克"],
    "Hugging Face": ["hugging face", "哈金费斯", "拥抱脸"],
    "Home Assistant": ["home system", "home assistant", "homeassistant", "霍姆系统", "家庭助手", "home assist"],
    "Kubernetes": ["k8s", "酷伯奈特斯", "库伯奈特斯", "kubernetes"],
}


def format_hotwords_for_llm(hotwords: list, max_words: int = 20) -> str:
    """
    格式化热词为LLM易读的对照表格式

    Args:
        hotwords: 热词列表
        max_words: 最多返回多少个热词

    Returns:
        格式化后的热词对照表字符串
    """
    # 筛选出有变体的热词
    mappings = []

    for word in hotwords:
        if word in HOTWORD_VARIANTS:
            variants = HOTWORD_VARIANTS[word][:3]  # 只取前3个最常见的
            for variant in variants:
                mappings.append(f"{variant} → {word}")

    # 只返回前max_words个映射
    return "\n".join(mappings[:max_words])


def get_variants(word: str) -> list:
    """
    获取某个热词的所有常见误识别变体

    Args:
        word: 热词

    Returns:
        变体列表
    """
    return HOTWORD_VARIANTS.get(word, [])


def find_correct_form(text: str) -> str:
    """
    查找文本对应的正确专有名词形式

    Args:
        text: 可能的误识别文本

    Returns:
        正确形式，如果没找到则返回原文本
    """
    text_lower = text.lower().strip()

    for correct, variants in HOTWORD_VARIANTS.items():
        # 检查是否与某个变体匹配
        for variant in variants:
            if text_lower == variant.lower():
                return correct

    return text


if __name__ == "__main__":
    # 测试
    print("🧪 测试热词变体映射\n")

    test_cases = [
        "千win三",
        "jmine",
        "i adit",
        "拍吐气",
        "x点com",
    ]

    print("误识别 → 正确形式:")
    for test in test_cases:
        correct = find_correct_form(test)
        print(f"  {test:15s} → {correct}")

    print("\n" + "="*50)
    print("格式化的热词上下文示例：\n")

    example_hotwords = ["Gemma", "Qwen3", "Reddit", "PyTorch", "Facebook"]
    formatted = format_hotwords_for_llm(example_hotwords)
    print(formatted)
