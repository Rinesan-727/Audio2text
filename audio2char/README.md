# 音频处理和思维导图生成工具

这是一个完整的音频处理和思维导图生成工具，支持多种音频格式的转写和智能分析，同时支持云端和本地部署。

## 🚀 功能特性

- **🎵 多格式音频支持**: wav、mp3、m4a、flac、aac、ogg
- **🧠 智能思维导图**: 基于 AI 的对话分析和可视化
- **👥 说话人分离**: 自动识别和分离不同说话人
- **⚡ 自动化流程**: 一键完成从音频到思维导图的完整处理
- **🌐 Web界面操作**: 直观的Web界面，支持拖拽上传
- **📱 实时进度显示**: 实时显示处理进度
- **💾 结果自动打包下载**: 自动打包处理结果
- **🛡️ 错误恢复**: 多级错误处理和备用方案
- **📊 详细报告**: 完整的处理摘要和质量评估
- **🏠 本地部署**: 支持完全本地化部署，保护数据隐私
- **🔄 混合模式**: 支持云端和本地模型的灵活切换

## 📁 项目结构

```
audio2char/
├── audio_web_app.py          # 一体化Web应用（主程序）
├── main.py                   # 音频处理脚本（包含说话人分离）
├── make_grapth.py            # 思维导图生成脚本
├── local_model_interface.py  # 本地模型接口
├── config.env.example        # 配置文件模板
├── config.env                # 配置文件（需要用户创建）
├── requirements_web.txt      # Python依赖列表
├── .gitignore               # Git忽略文件
├── output/                   # 输出目录
│   └── mindmap.html          # 生成的思维导图
├── templates/                # Web模板
├── static/                   # 静态文件
└── transcripts_*/            # 转写结果目录
    ├── full_transcript.txt
    └── summary.txt
```

## 🛠️ 快速开始

### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements_web.txt

# 安装系统依赖（Ubuntu/Debian）
sudo apt update
sudo apt install ffmpeg sox

# macOS
brew install ffmpeg sox

# Windows
# 下载并安装 ffmpeg 和 sox
```

### 2. 配置

```bash
# 复制配置文件模板
cp config.env.example config.env

# 编辑 config.env，填入你的API密钥
```

### 3. 启动Web应用

```bash
python audio_web_app.py --web
```

### 4. 访问界面

打开浏览器访问：http://localhost:5000

## ⚙️ 配置说明

### 云端部署配置

在 `config.env` 中配置你的 API 密钥：

```env
# 硅基流动API配置
API_KEY=your-api-key-here
API_URL=https://api.siliconflow.cn/v1/chat/completions
MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
```

### 本地部署配置

配置本地模型：

```env
# 启用本地模型
USE_LOCAL_MODEL=true
LOCAL_MODEL_TYPE=ollama
LOCAL_MODEL_NAME=qwen2.5:7b

# 云端API作为备用
API_KEY=your-backup-api-key
API_URL=https://api.siliconflow.cn/v1/chat/completions
MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
```

### 其他配置参数

- `API_KEY`: 你的API密钥
- `USE_LOCAL_MODEL`: 是否使用本地模型
- `LOCAL_MODEL_TYPE`: 本地模型类型 (ollama/lmstudio/vllm)
- `MAX_FILE_SIZE`: 最大文件大小 (MB)
- `WHISPER_MODEL_SIZE`: Whisper模型大小

### 🔒 安全说明

- `config.env` 文件包含敏感信息，已被添加到 `.gitignore`
- 请勿将你的真实API密钥提交到版本控制系统
- 使用 `config.env.example` 作为配置模板

## 🏠 本地部署指南

### 部署前准备

#### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 4核心 | 8核心以上 |
| 内存 | 8GB | 16GB以上 |
| 存储 | 10GB | 20GB以上 |
| GPU | 可选 | NVIDIA GTX 1060+ |

#### 软件要求

- **操作系统**: Ubuntu 20.04+, Windows 10+, macOS 10.15+
- **Python**: 3.8+
- **CUDA**: 11.8+ (可选，用于GPU加速)

### 快速部署步骤

#### 步骤1: 安装本地大模型

**方案A: Ollama (推荐)**

```bash
# 安装Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 启动Ollama服务
ollama serve

# 下载模型 (新终端)
ollama pull qwen2.5:7b
```

**方案B: LM Studio**

1. 下载 [LM Studio](https://lmstudio.ai/)
2. 安装并启动
3. 下载模型到本地
4. 启动本地服务器

**方案C: vLLM**

```bash
pip install vllm
vllm serve qwen2.5-7b --host 0.0.0.0 --port 8000
```

#### 步骤2: 配置环境

```bash
# 复制配置文件
cp config_local.env config.env

# 编辑配置文件
nano config.env
```

#### 步骤3: 测试部署

```bash
# 测试本地模型连接
python local_model_interface.py

# 测试完整流程
python app.py --audio-only
```

### 详细配置

#### Ollama配置

```bash
# 查看可用模型
ollama list

# 下载其他模型
ollama pull llama2:7b
ollama pull mistral:7b
ollama pull qwen2.5:14b

# 自定义模型配置
ollama create mymodel -f Modelfile
```

#### LM Studio配置

1. **模型下载**:
   - 在LM Studio中搜索并下载模型
   - 推荐: Qwen2.5-7B, Llama2-7B, Mistral-7B

2. **服务器配置**:
   - 端口: 1234 (默认)
   - 上下文长度: 4096
   - 批处理大小: 1

#### vLLM配置

```bash
# 启动vLLM服务器
vllm serve qwen2.5-7b \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 1 \
    --max-model-len 4096

# 多GPU配置
vllm serve qwen2.5-7b \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 2 \
    --max-model-len 8192
```

### 测试和验证

#### 测试本地模型接口

```bash
python local_model_interface.py
```

预期输出：
```
=== 测试Ollama ===
🧪 测试 ollama 连接...
✅ ollama 连接成功
📝 测试响应: 连接成功...

=== 测试LM Studio ===
🧪 测试 lmstudio 连接...
✅ lmstudio 连接成功
```

### 故障排除

#### 常见问题

**1. Ollama连接失败**

```bash
# 检查Ollama服务状态
ollama list

# 重启Ollama服务
sudo systemctl restart ollama

# 检查端口
netstat -tlnp | grep 11434
```

**2. 模型下载失败**

```bash
# 清理缓存
ollama rm qwen2.5:7b

# 重新下载
ollama pull qwen2.5:7b

# 检查网络连接
curl -I https://ollama.ai
```

**3. 内存不足**

```bash
# 使用更小的模型
ollama pull qwen2.5:3b

# 或使用量化版本
ollama pull qwen2.5:7b-q4_K_M
```

**4. GPU内存不足**

```bash
# 使用CPU模式
export CUDA_VISIBLE_DEVICES=""

# 或使用更小的模型
ollama pull qwen2.5:3b
```

#### 性能优化

**1. GPU加速**

```bash
# 检查CUDA可用性
python -c "import torch; print(torch.cuda.is_available())"

# 设置GPU内存分配
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

**2. 模型优化**

```bash
# 使用量化模型
ollama pull qwen2.5:7b-q4_K_M

# 或使用更小的模型
ollama pull qwen2.5:3b
```

**3. 系统优化**

```bash
# 增加交换空间
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 性能对比

| 部署方式 | 响应速度 | 准确率 | 成本 | 隐私性 |
|---------|---------|--------|------|--------|
| 完全云端 | 快 | 高 | 高 | 低 |
| 混合部署 | 中 | 高 | 中 | 中 |
| 完全本地 | 中 | 中 | 低 | 高 |

### 安全考虑

#### 数据隐私

- ✅ 所有数据在本地处理
- ✅ 无需网络连接
- ✅ 完全离线运行

#### 网络安全

```bash
# 限制本地服务访问
# 只允许本地访问
vllm serve qwen2.5-7b --host 127.0.0.1 --port 8000

# 或使用防火墙
sudo ufw allow from 127.0.0.1 to any port 8000
```

## 🎯 使用方法

### 命令行使用

```bash
# 处理音频文件
python audio_web_app.py --audio your_file.mp3

# 仅生成思维导图
python audio_web_app.py --graph-only --transcript transcripts_xxx

# 仅处理音频
python audio_web_app.py --audio your_file.mp3 --audio-only
```

### Web界面模式（推荐）

```bash
# 启动Web服务器
python audio_web_app.py --web

# 指定端口启动
python audio_web_app.py --web --port 8080

# 指定主机和端口
python audio_web_app.py --web --host 0.0.0.0 --port 8080
```

访问 `http://localhost:5000` 使用Web界面。

### 命令行模式

```bash
# 完整流程（推荐）
python audio_web_app.py

# 指定音频文件
python audio_web_app.py --audio "你的音频文件.mp3"

# 仅处理音频，不生成思维导图
python audio_web_app.py --audio-only

# 仅生成思维导图，使用现有转写目录
python audio_web_app.py --graph-only --transcript transcripts_20250825_120404
```

### 详细用法

#### 1. 完整流程
```bash
python app.py
```
- 自动检测音频文件
- 处理音频并生成转写
- 生成思维导图
- 显示处理摘要

#### 2. 指定音频文件
```bash
python app.py --audio "path/to/your/audio.mp3"
```
- 处理指定的音频文件
- 支持相对路径和绝对路径

#### 3. 仅音频处理
```bash
python app.py --audio-only
```
- 只进行音频转写
- 不生成思维导图
- 适合批量处理音频文件

#### 4. 仅思维导图生成
```bash
python app.py --graph-only --transcript transcripts_20250825_120404
```
- 使用现有的转写结果
- 仅生成思维导图
- 适合重新分析已有数据

## 📊 输出文件

### 转写结果
- `transcripts_YYYYMMDD_HHMMSS/`
  - `full_transcript.txt`: 完整转写文本
  - `summary.txt`: 汇总报告

### 思维导图
- `output/mindmap.html`: 交互式思维导图
  - 支持缩放和拖拽
  - 点击节点查看详情
  - 响应式设计

### 打包结果
- `results_*.zip`: 自动打包的结果文件

### 输出文件说明

- `transcripts_*/`: 转写结果目录
- `output/mindmap.html`: 思维导图
- `results_*.zip`: 打包结果文件

## 🔧 高级配置

### 音频处理参数
在 `main_simple.py` 中可以调整：
- 模型大小：`tiny`, `base`, `small`, `medium`, `large`
- 采样率：默认 16kHz
- 声道数：默认单声道

### 思维导图参数
在 `make_grapth.py` 中可以调整：
- API 模型选择
- 思维导图样式
- 分析深度

## 🐛 故障排除

### 常见问题

1. **音频转换失败**
   ```bash
   # 确保安装了 ffmpeg
   sudo apt install ffmpeg
   ```

2. **API 调用失败**
   - 检查 `config.env` 中的 API 配置
   - 确认 API 密钥有效
   - 检查网络连接

3. **内存不足**
   - 使用较小的模型：`tiny` 或 `base`
   - 减少音频文件大小
   - 使用 CPU 模式

### 错误日志
- 查看控制台输出的详细错误信息
- 检查生成的文件是否完整
- 确认文件权限正确

## 📈 性能优化

### GPU 加速
- 自动检测 CUDA 可用性
- 支持 GPU 加速转写
- 大幅提升处理速度

### 批量处理
```bash
# 处理多个音频文件
for file in *.mp3; do
    python app.py --audio "$file" --audio-only
done
```

## 🎯 使用建议

### 生产环境

1. **高可用性**: 配置云端API作为备用
2. **监控**: 监控本地服务状态
3. **备份**: 定期备份模型和配置
4. **更新**: 定期更新模型版本

### 开发环境

1. **快速迭代**: 使用小模型进行开发
2. **调试**: 启用详细日志
3. **测试**: 建立自动化测试流程

