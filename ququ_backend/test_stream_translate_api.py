#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试流式翻译API接口
用于验证 /api/asr/transcribe-and-translate-stream 的功能
"""

import asyncio
import aiohttp
import sys
from pathlib import Path


async def test_stream_translate_api(audio_file: str, source_lang: str = "中文", target_lang: str = "英文"):
    """测试流式翻译API"""

    if not Path(audio_file).exists():
        print(f"❌ 音频文件不存在: {audio_file}")
        return

    url = "http://localhost:8000/api/asr/transcribe-and-translate-stream"

    print(f"📤 上传音频: {audio_file}")
    print(f"🌐 连接到: {url}")
    print(f"🔄 翻译方向: {source_lang} → {target_lang}")
    print("-" * 60)

    try:
        # 准备表单数据
        with open(audio_file, 'rb') as f:
            audio_data = f.read()

        form_data = aiohttp.FormData()
        form_data.add_field('audio',
                           audio_data,
                           filename=Path(audio_file).name,
                           content_type='audio/mpeg')
        form_data.add_field('use_vad', 'true')
        form_data.add_field('use_punc', 'true')
        form_data.add_field('hotword', '')
        form_data.add_field('source_lang', source_lang)
        form_data.add_field('target_lang', target_lang)

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=form_data) as response:
                if response.status != 200:
                    print(f"❌ 请求失败: HTTP {response.status}")
                    error_text = await response.text()
                    print(f"错误信息: {error_text}")
                    return

                print("✅ 连接成功，开始接收流式数据...\n")

                # 读取SSE流
                async for line in response.content:
                    line = line.decode('utf-8').strip()

                    if line.startswith('data: '):
                        data_str = line[6:]  # 移除 'data: ' 前缀

                        try:
                            import json
                            data = json.loads(data_str)
                            stage = data.get('stage', 'unknown')

                            if stage == 'start':
                                print(f"🚀 [{stage}] {data.get('message')}")

                            elif stage == 'asr_complete':
                                print(f"🎤 [{stage}] ASR识别完成:")
                                print(f"   文本: {data.get('text')}")
                                print(f"   时长: {data.get('duration', 0):.2f}秒")

                            elif stage == 'translating':
                                print(f"🔄 [{stage}] {data.get('message')}")

                            elif stage == 'translate_complete':
                                print(f"🌍 [{stage}] 翻译完成:")
                                print(f"   译文: {data.get('text')}")

                            elif stage == 'done':
                                print(f"✅ [{stage}] {data.get('message')}")
                                print("\n" + "=" * 60)
                                print("📊 最终结果:")
                                print(f"   原文 ({data.get('source_lang')}): {data.get('asr_text')}")
                                print(f"   译文 ({data.get('target_lang')}): {data.get('translated_text')}")
                                print("=" * 60)

                            elif stage == 'error':
                                print(f"❌ [{stage}] 错误: {data.get('error')}")

                            else:
                                print(f"⚪ [{stage}] {data}")

                            print()  # 空行分隔

                        except json.JSONDecodeError as e:
                            print(f"⚠️ JSON解析错误: {e}")
                            print(f"   原始数据: {data_str}")

    except aiohttp.ClientError as e:
        print(f"❌ 网络错误: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python test_stream_translate_api.py <audio_file> [source_lang] [target_lang]")
        print("\n示例:")
        print("  python test_stream_translate_api.py test.wav")
        print("  python test_stream_translate_api.py test.mp3 中文 英文")
        print("  python test_stream_translate_api.py test.mp3 英文 中文")
        sys.exit(1)

    audio_file = sys.argv[1]
    source_lang = sys.argv[2] if len(sys.argv) > 2 else "中文"
    target_lang = sys.argv[3] if len(sys.argv) > 3 else "英文"

    await test_stream_translate_api(audio_file, source_lang, target_lang)


if __name__ == "__main__":
    asyncio.run(main())
