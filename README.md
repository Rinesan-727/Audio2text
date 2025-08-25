# Audio Processing and Mind Map Generation Tool

A comprehensive audio processing and mind map generation tool that supports transcription and intelligent analysis of multiple audio formats, with both cloud and local deployment options.

## 🚀 Features

- **🎵 Multi-format Audio Support**: wav, mp3, m4a, flac, aac, ogg
- **🧠 Intelligent Mind Maps**: AI-based conversation analysis and visualization
- **👥 Speaker Separation**: Automatic identification and separation of different speakers
- **⚡ Automated Workflow**: One-click complete processing from audio to mind map
- **🌐 Web Interface**: Intuitive web interface with drag-and-drop upload
- **📱 Real-time Progress**: Real-time processing progress display
- **💾 Auto-packaging**: Automatic packaging and download of results
- **🛡️ Error Recovery**: Multi-level error handling and fallback solutions
- **📊 Detailed Reports**: Complete processing summaries and quality assessments
- **🏠 Local Deployment**: Support for complete local deployment, protecting data privacy
- **🔄 Hybrid Mode**: Flexible switching between cloud and local models

## 📁 Project Structure

```
audio2char/
├── audio_web_app.py          # Integrated Web Application (Main Program)
├── main.py                   # Audio Processing Script (with Speaker Separation)
├── make_grapth.py            # Mind Map Generation Script
├── local_model_interface.py  # Local Model Interface
├── config.env.example        # Configuration File Template
├── config.env                # Configuration File (User Created)
├── requirements_web.txt      # Python Dependencies
├── .gitignore               # Git Ignore File
├── output/                   # Output Directory
│   └── mindmap.html          # Generated Mind Map
├── templates/                # Web Templates
├── static/                   # Static Files
└── transcripts_*/            # Transcription Results Directory
    ├── full_transcript.txt
    └── summary.txt
```

## 🛠️ Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements_web.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt update
sudo apt install ffmpeg sox

# macOS
brew install ffmpeg sox

# Windows
# Download and install ffmpeg and sox
```

### 2. Configuration

```bash
# Copy configuration file template
cp config.env.example config.env

# Edit config.env and enter your API key
```

### 3. Start Web Application

```bash
python audio_web_app.py --web
```

### 4. Access Interface

Open your browser and visit: http://localhost:5000

## ⚙️ Configuration

### Cloud Deployment Configuration

Configure your API key in `config.env`:

```env
# SiliconFlow API Configuration
API_KEY=your-api-key-here
API_URL=https://api.siliconflow.cn/v1/chat/completions
MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
```

### Local Deployment Configuration

Configure local models:

```env
# Enable local model
USE_LOCAL_MODEL=true
LOCAL_MODEL_TYPE=ollama
LOCAL_MODEL_NAME=qwen2.5:7b

# Cloud API as backup
API_KEY=your-backup-api-key
API_URL=https://api.siliconflow.cn/v1/chat/completions
MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
```

### Other Configuration Parameters

- `API_KEY`: Your API key
- `USE_LOCAL_MODEL`: Whether to use local model
- `LOCAL_MODEL_TYPE`: Local model type (ollama/lmstudio/vllm)
- `MAX_FILE_SIZE`: Maximum file size (MB)
- `WHISPER_MODEL_SIZE`: Whisper model size

### 🔒 Security Notes

- The `config.env` file contains sensitive information and has been added to `.gitignore`
- Do not commit your real API keys to version control
- Use `config.env.example` as a configuration template

## 🏠 Local Deployment Guide

### Pre-deployment Requirements

#### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8GB | 16GB+ |
| Storage | 10GB | 20GB+ |
| GPU | Optional | NVIDIA GTX 1060+ |

#### Software Requirements

- **Operating System**: Ubuntu 20.04+, Windows 10+, macOS 10.15+
- **Python**: 3.8+
- **CUDA**: 11.8+ (optional, for GPU acceleration)

### Quick Deployment Steps

#### Step 1: Install Local Large Models

**Option A: Ollama (Recommended)**

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Download model (new terminal)
ollama pull qwen2.5:7b
```

**Option B: LM Studio**

1. Download [LM Studio](https://lmstudio.ai/)
2. Install and start
3. Download models locally
4. Start local server

**Option C: vLLM**

```bash
pip install vllm
vllm serve qwen2.5-7b --host 0.0.0.0 --port 8000
```

#### Step 2: Configure Environment

```bash
# Copy configuration file
cp config_local.env config.env

# Edit configuration file
nano config.env
```

#### Step 3: Test Deployment

```bash
# Test local model connection
python local_model_interface.py

# Test complete workflow
python app.py --audio-only
```

### Detailed Configuration

#### Ollama Configuration

```bash
# View available models
ollama list

# Download other models
ollama pull llama2:7b
ollama pull mistral:7b
ollama pull qwen2.5:14b

# Custom model configuration
ollama create mymodel -f Modelfile
```

#### LM Studio Configuration

1. **Model Download**:
   - Search and download models in LM Studio
   - Recommended: Qwen2.5-7B, Llama2-7B, Mistral-7B

2. **Server Configuration**:
   - Port: 1234 (default)
   - Context length: 4096
   - Batch size: 1

#### vLLM Configuration

```bash
# Start vLLM server
vllm serve qwen2.5-7b \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 1 \
    --max-model-len 4096

# Multi-GPU configuration
vllm serve qwen2.5-7b \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 2 \
    --max-model-len 8192
```

### Testing and Validation

#### Test Local Model Interface

```bash
python local_model_interface.py
```

Expected output:
```
=== Testing Ollama ===
🧪 Testing ollama connection...
✅ ollama connection successful
📝 Test response: Connection successful...

=== Testing LM Studio ===
🧪 Testing lmstudio connection...
✅ lmstudio connection successful
```

### Troubleshooting

#### Common Issues

**1. Ollama Connection Failure**

```bash
# Check Ollama service status
ollama list

# Restart Ollama service
sudo systemctl restart ollama

# Check port
netstat -tlnp | grep 11434
```

**2. Model Download Failure**

```bash
# Clear cache
ollama rm qwen2.5:7b

# Re-download
ollama pull qwen2.5:7b

# Check network connection
curl -I https://ollama.ai
```

**3. Insufficient Memory**

```bash
# Use smaller model
ollama pull qwen2.5:3b

# Or use quantized version
ollama pull qwen2.5:7b-q4_K_M
```

**4. GPU Memory Insufficient**

```bash
# Use CPU mode
export CUDA_VISIBLE_DEVICES=""

# Or use smaller model
ollama pull qwen2.5:3b
```

#### Performance Optimization

**1. GPU Acceleration**

```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Set GPU memory allocation
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

**2. Model Optimization**

```bash
# Use quantized models
ollama pull qwen2.5:7b-q4_K_M

# Or use smaller models
ollama pull qwen2.5:3b
```

**3. System Optimization**

```bash
# Increase swap space
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Performance Comparison

| Deployment Method | Response Speed | Accuracy | Cost | Privacy |
|------------------|----------------|----------|------|---------|
| Full Cloud | Fast | High | High | Low |
| Hybrid Deployment | Medium | High | Medium | Medium |
| Full Local | Medium | Medium | Low | High |

### Security Considerations

#### Data Privacy

- ✅ All data processed locally
- ✅ No network connection required
- ✅ Completely offline operation

#### Network Security

```bash
# Restrict local service access
# Only allow local access
vllm serve qwen2.5-7b --host 127.0.0.1 --port 8000

# Or use firewall
sudo ufw allow from 127.0.0.1 to any port 8000
```

## 🎯 Usage

### Command Line Usage

```bash
# Process audio file
python audio_web_app.py --audio your_file.mp3

# Generate mind map only
python audio_web_app.py --graph-only --transcript transcripts_xxx

# Process audio only
python audio_web_app.py --audio your_file.mp3 --audio-only
```

### Web Interface Mode (Recommended)

```bash
# Start web server
python audio_web_app.py --web

# Start with specific port
python audio_web_app.py --web --port 8080

# Start with specific host and port
python audio_web_app.py --web --host 0.0.0.0 --port 8080
```

Visit `http://localhost:5000` to use the web interface.

### Command Line Mode

```bash
# Complete workflow (recommended)
python audio_web_app.py

# Specify audio file
python audio_web_app.py --audio "your_audio_file.mp3"

# Process audio only, no mind map generation
python audio_web_app.py --audio-only

# Generate mind map only, using existing transcript directory
python audio_web_app.py --graph-only --transcript transcripts_20250825_120404
```

### Detailed Usage

#### 1. Complete Workflow
```bash
python app.py
```
- Automatically detect audio files
- Process audio and generate transcriptions
- Generate mind maps
- Display processing summary

#### 2. Specify Audio File
```bash
python app.py --audio "path/to/your/audio.mp3"
```
- Process specified audio file
- Support relative and absolute paths

#### 3. Audio Processing Only
```bash
python app.py --audio-only
```
- Only perform audio transcription
- No mind map generation
- Suitable for batch processing audio files

#### 4. Mind Map Generation Only
```bash
python app.py --graph-only --transcript transcripts_20250825_120404
```
- Use existing transcription results
- Generate mind map only
- Suitable for re-analyzing existing data

## 📊 Output Files

### Transcription Results
- `transcripts_YYYYMMDD_HHMMSS/`
  - `full_transcript.txt`: Complete transcription text
  - `summary.txt`: Summary report

### Mind Map
- `output/mindmap.html`: Interactive mind map
  - Support zoom and drag
  - Click nodes to view details
  - Responsive design

### Packaged Results
- `results_*.zip`: Auto-packaged result files

### Output File Description

- `transcripts_*/`: Transcription results directory
- `output/mindmap.html`: Mind map
- `results_*.zip`: Packaged result files

## 🔧 Advanced Configuration

### Audio Processing Parameters
Adjustable in `main_simple.py`:
- Model size: `tiny`, `base`, `small`, `medium`, `large`
- Sample rate: Default 16kHz
- Channels: Default mono

### Mind Map Parameters
Adjustable in `make_grapth.py`:
- API model selection
- Mind map style
- Analysis depth

## 🐛 Troubleshooting

### Common Issues

1. **Audio Conversion Failure**
   ```bash
   # Ensure ffmpeg is installed
   sudo apt install ffmpeg
   ```

2. **API Call Failure**
   - Check API configuration in `config.env`
   - Confirm API key is valid
   - Check network connection

3. **Insufficient Memory**
   - Use smaller models: `tiny` or `base`
   - Reduce audio file size
   - Use CPU mode

### Error Logs
- View detailed error information in console output
- Check if generated files are complete
- Confirm file permissions are correct

## 📈 Performance Optimization

### GPU Acceleration
- Automatic CUDA availability detection
- Support GPU-accelerated transcription
- Significantly improve processing speed

### Batch Processing
```bash
# Process multiple audio files
for file in *.mp3; do
    python app.py --audio "$file" --audio-only
done
```

## 🎯 Usage Recommendations

### Production Environment

1. **High Availability**: Configure cloud API as backup
2. **Monitoring**: Monitor local service status
3. **Backup**: Regularly backup models and configurations
4. **Updates**: Regularly update model versions

### Development Environment

1. **Rapid Iteration**: Use small models for development
2. **Debugging**: Enable detailed logging
3. **Testing**: Establish automated testing workflow
