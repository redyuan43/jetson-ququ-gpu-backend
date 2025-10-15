#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU加速测试脚本
验证FunASR在GPU模式下的工作状态
"""

import sys
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_pytorch_gpu():
    """测试PyTorch GPU支持"""
    logger.info("=" * 60)
    logger.info("测试1: PyTorch GPU支持")
    logger.info("=" * 60)

    try:
        import torch

        logger.info(f"PyTorch版本: {torch.__version__}")
        logger.info(f"CUDA可用: {torch.cuda.is_available()}")

        if torch.cuda.is_available():
            logger.info(f"CUDA版本: {torch.version.cuda}")
            logger.info(f"GPU数量: {torch.cuda.device_count()}")
            logger.info(f"当前GPU: {torch.cuda.current_device()}")
            logger.info(f"GPU名称: {torch.cuda.get_device_name(0)}")
            logger.info(f"GPU显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
            return True
        else:
            logger.error("❌ CUDA不可用！")
            return False

    except Exception as e:
        logger.error(f"❌ PyTorch测试失败: {str(e)}")
        return False


def test_funasr_import():
    """测试FunASR导入"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试2: FunASR导入")
    logger.info("=" * 60)

    try:
        import funasr
        from funasr import AutoModel

        logger.info(f"✅ FunASR版本: {getattr(funasr, '__version__', 'unknown')}")
        logger.info("✅ AutoModel导入成功")
        return True

    except Exception as e:
        logger.error(f"❌ FunASR导入失败: {str(e)}")
        return False


def test_funasr_gpu_loading():
    """测试FunASR GPU模式加载"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试3: FunASR GPU模式加载")
    logger.info("=" * 60)

    try:
        from funasr import AutoModel
        import torch

        logger.info("加载ASR模型到GPU...")
        start_time = time.time()

        model = AutoModel(
            model="damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
            model_revision="v2.0.4",
            disable_update=True,
            device="cuda:0"
        )

        load_time = time.time() - start_time
        logger.info(f"✅ 模型加载成功！耗时: {load_time:.2f}秒")

        # 检查模型确实在GPU上
        if hasattr(model, 'model'):
            device = next(model.model.parameters()).device
            logger.info(f"✅ 模型设备: {device}")

            if device.type == 'cuda':
                logger.info("✅ 确认：模型在GPU上运行")
                return True
            else:
                logger.warning("⚠️ 模型不在GPU上！")
                return False
        else:
            logger.info("✅ 模型加载成功（无法检测设备）")
            return True

    except Exception as e:
        logger.error(f"❌ FunASR GPU加载失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_full_pipeline():
    """测试完整的FunASR GPU管理器"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试4: FunASR GPU管理器")
    logger.info("=" * 60)

    try:
        from funasr_gpu import FunASRServer

        logger.info("初始化FunASR GPU服务器...")
        server = FunASRServer()

        logger.info("开始初始化模型...")
        start_time = time.time()

        result = server.initialize()

        init_time = time.time() - start_time

        if result["success"]:
            logger.info(f"✅ 初始化成功！总耗时: {init_time:.2f}秒")
            logger.info(f"   消息: {result.get('message')}")

            # 获取性能统计
            stats = server.get_performance_stats()
            logger.info(f"   模型状态:")
            logger.info(f"     - ASR: {stats['models_loaded']['asr']}")
            logger.info(f"     - VAD: {stats['models_loaded']['vad']}")
            logger.info(f"     - PUNC: {stats['models_loaded']['punc']}")

            return True
        else:
            logger.error(f"❌ 初始化失败: {result.get('error')}")
            return False

    except Exception as e:
        logger.error(f"❌ FunASR GPU管理器测试失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_gpu_memory():
    """测试GPU显存使用"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试5: GPU显存监控")
    logger.info("=" * 60)

    try:
        import torch

        if not torch.cuda.is_available():
            logger.warning("⚠️ CUDA不可用，跳过显存测试")
            return True

        allocated = torch.cuda.memory_allocated(0) / 1024**3
        reserved = torch.cuda.memory_reserved(0) / 1024**3
        total = torch.cuda.get_device_properties(0).total_memory / 1024**3

        logger.info(f"GPU显存使用情况:")
        logger.info(f"  - 已分配: {allocated:.2f} GB")
        logger.info(f"  - 已预留: {reserved:.2f} GB")
        logger.info(f"  - 总容量: {total:.2f} GB")
        logger.info(f"  - 使用率: {(allocated/total)*100:.1f}%")

        if allocated > 0:
            logger.info("✅ GPU显存有分配（模型已加载到GPU）")
        else:
            logger.warning("⚠️ GPU显存未分配（模型可能未在GPU上）")

        return True

    except Exception as e:
        logger.error(f"❌ GPU显存测试失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    logger.info("\n\n")
    logger.info("🚀 开始GPU加速FunASR测试")
    logger.info("=" * 60)

    results = {}

    # 执行所有测试
    results["PyTorch GPU"] = test_pytorch_gpu()
    results["FunASR导入"] = test_funasr_import()
    results["FunASR GPU加载"] = test_funasr_gpu_loading()
    results["FunASR管理器"] = test_full_pipeline()
    results["GPU显存"] = test_gpu_memory()

    # 总结
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")

    logger.info("")
    logger.info(f"总计: {passed}/{total} 测试通过")

    if passed == total:
        logger.info("🎉 所有测试通过！GPU加速FunASR工作正常")
        return 0
    else:
        logger.error(f"⚠️ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
