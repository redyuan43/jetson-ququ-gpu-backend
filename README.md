----------------------------------------------------------------------
docker-compose up -d deepresearch-runner

##Verify it's running:

  docker-compose ps

  ## Then access the container:

  docker exec -it deepresearch-runner bash


docker exec -it deepresearch-runner bash
./llama.cpp/build/bin/llama-cli     --model current_model.gguf     --ctx-size 81920     --n-gpu-layers 48     --threads 12  
   --temp 0.7     --prompt "请介绍阿里巴巴的WebAgent技术" 

------------------------------------
 🔧 核心执行指令

  1. 启动模型服务器

  docker exec deepresearch-runner bash -c "export LD_LIBRARY_PATH=/workspace/llama.cpp/build/bin:$LD_LIBRARY_PATH && 
  /workspace/llama.cpp/build/bin/llama-server --model /workspace/models/Alibaba-NLP_Tongyi-DeepResearch-30B-A3B-Q4_K_M.gguf --ctx-size 8192 
  --n-gpu-layers 48 --port 8004 --host 0.0.0.0 > /tmp/server.log 2>&1 &"

  2. 启动Web界面（已修改配置）

  docker exec deepresearch-runner bash -c "cd /workspace/DeepResearch/WebAgent/WebDancer && export GOOGLE_SEARCH_KEY='' && export 
  JINA_API_KEY='' && export DASHSCOPE_API_KEY='' && python3 -m demos.assistant_qwq_chat > /tmp/web.log 2>&1 &"

  3. 远程访问地址

  - 主地址: http://192.168.100.38:7860
  - 备用地址: http://192.168.100.126:7860
  - 公共URL: https://1eb3fe6a114a4c117f.gradio.live (72小时内有效)

  4. 状态检查

  # 检查服务状态
  docker exec deepresearch-runner bash -c "ps aux | grep -E 'llama-server|assistant_qwq' | grep -v grep"

  # 检查端口监听
  ss -tlnp | grep 7860

  # 查看Web日志
  docker exec deepresearch-runner bash -c "tail -20 /tmp/web.log"

  # 查看模型服务器日志
  docker exec deepresearch-runner bash -c "tail -20 /tmp/server.log"

  💡 使用提示

  1. 忽略搜索功能: 由于未配置API密钥，搜索功能会报错，但对话功能正常
  2. 测试对话: 直接输入中文问题进行测试
  3. 预设问题: 界面有多个预设测试问题可用
  4. 性能: 基于30B模型，响应可能需要一些时间

  Web界面已就绪，您现在可以通过 http://192.168.100.38:7860 远程访问DeepResearch的WebAgent界面了！
