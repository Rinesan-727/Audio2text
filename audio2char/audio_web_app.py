#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频转文字Web应用 - 一体化版本
整合了音频处理和Web界面功能
"""

import os
import sys
import json
import shutil
import subprocess
import threading
import zipfile
import re
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, send_file
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename

# 加载配置文件
load_dotenv('config.env')

# 导入本地模型接口
try:
    from local_model_interface import create_local_model_interface
    LOCAL_MODEL_AVAILABLE = True
except ImportError:
    LOCAL_MODEL_AVAILABLE = False

class AudioProcessor:
    """音频处理和思维导图生成的控制器"""
    
    def __init__(self):
        self.audio_script = "main.py"
        self.graph_script = "make_grapth.py"
        self.output_dir = None
        self.summary_file = None
        
        # 本地模型配置
        self.use_local_model = os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"
        self.local_model_type = os.getenv("LOCAL_MODEL_TYPE", "ollama")
        self.local_model_name = os.getenv("LOCAL_MODEL_NAME", "qwen2.5:7b")
    
    def find_latest_transcript_dir(self):
        """查找最新的转写结果目录"""
        transcript_dirs = []
        
        # 检查当前目录
        for item in os.listdir('.'):
            if item.startswith('transcripts_') and os.path.isdir(item):
                transcript_dirs.append(item)
        
        if not transcript_dirs:
            return None
        
        # 按时间戳排序，获取最新的
        latest_dir = max(transcript_dirs, key=os.path.getctime)
        return latest_dir
    
    def set_local_model_env(self):
        """设置本地模型环境变量"""
        if self.use_local_model and LOCAL_MODEL_AVAILABLE:
            os.environ["USE_LOCAL_MODEL"] = "true"
            os.environ["LOCAL_MODEL_TYPE"] = self.local_model_type
            os.environ["LOCAL_MODEL_NAME"] = self.local_model_name
        else:
            os.environ["USE_LOCAL_MODEL"] = "false"
    
    def update_graph_script_path(self, transcript_dir):
        """更新make_grapth.py中的转写目录路径"""
        try:
            # 读取make_grapth.py文件
            with open(self.graph_script, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 更新目录路径 - 使用相对路径
            pattern = r'specific_dir = "[^"]*"'
            replacement = f'specific_dir = "{transcript_dir}"'
            
            new_content = re.sub(pattern, replacement, content)
            
            # 写回文件
            with open(self.graph_script, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return True
        except Exception as e:
            print(f"更新脚本路径失败: {e}")
            return False

# 从配置文件读取设置
WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
WEB_PORT = int(os.getenv('WEB_PORT', '5000'))
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '500'))
SUPPORTED_FORMATS = os.getenv('SUPPORTED_FORMATS', 'wav,mp3,m4a,flac,aac,ogg').split(',')
WHISPER_MODEL_SIZE = os.getenv('WHISPER_MODEL_SIZE', 'medium')
MIN_SPEAKERS = int(os.getenv('MIN_SPEAKERS', '2'))
MAX_SPEAKERS = int(os.getenv('MAX_SPEAKERS', '5'))
MIN_SEGMENT_DURATION = float(os.getenv('MIN_SEGMENT_DURATION', '0.5'))

# Flask应用配置
app = Flask(__name__)
app.config['SECRET_KEY'] = 'audio-transcription-unified-app'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE * 1024 * 1024  # MB to bytes

# 创建上传目录
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 允许的音频文件扩展名
ALLOWED_EXTENSIONS = set(SUPPORTED_FORMATS)

# 全局音频处理器实例
audio_processor = AudioProcessor()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        file = request.files['audio']
        
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'不支持的文件格式，支持的格式：{", ".join(SUPPORTED_FORMATS)}'}), 400
        
        # 保存文件
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 启动后台处理任务
        task_id = timestamp
        thread = threading.Thread(target=process_audio_task, args=(filepath, filename, task_id))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'filename': filename,
            'message': '文件上传成功，正在处理中...'
        })
        
    except Exception as e:
        return jsonify({'error': f'上传失败：{str(e)}'}), 500

def process_audio_task(filepath, filename, task_id):
    """后台音频处理任务"""
    try:
        # 发送开始处理消息
        socketio.emit('progress', {
            'task_id': task_id,
            'stage': 'start',
            'message': '开始处理音频文件...',
            'progress': 5
        })
        
        # 复制文件到工作目录
        target_path = filename
        shutil.copy2(filepath, target_path)
        
        socketio.emit('progress', {
            'task_id': task_id,
            'stage': 'transcription',
            'message': '正在进行语音识别和说话人分离...',
            'progress': 15
        })
        
        # 步骤1: 调用音频处理程序
        cmd = ['conda', 'run', '-n', 'rag4', 'python', 'main.py']
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        # 实时读取输出并更新进度
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                if "正在加载说话人分离模型" in output:
                    socketio.emit('progress', {
                        'task_id': task_id,
                        'stage': 'diarization',
                        'message': '正在加载说话人分离模型...',
                        'progress': 25
                    })
                elif "正在加载语音识别模型" in output:
                    socketio.emit('progress', {
                        'task_id': task_id,
                        'stage': 'recognition',
                        'message': '正在加载语音识别模型...',
                        'progress': 40
                    })
                elif "转写结果已保存" in output:
                    socketio.emit('progress', {
                        'task_id': task_id,
                        'stage': 'transcription_complete',
                        'message': '语音转写完成',
                        'progress': 60
                    })
        
        # 等待音频处理完成
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"音频处理失败: {stderr}")
        
        # 查找生成的转写目录
        transcript_dir = audio_processor.find_latest_transcript_dir()
        if not transcript_dir:
            raise Exception("未找到转写结果目录")
        
        socketio.emit('progress', {
            'task_id': task_id,
            'stage': 'mindmap',
            'message': '正在生成思维导图...',
            'progress': 70
        })
        
        # 步骤2: 生成思维导图
        audio_processor.set_local_model_env()
        audio_processor.update_graph_script_path(transcript_dir)
        
        cmd = ['conda', 'run', '-n', 'rag4', 'python', 'make_grapth.py']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            raise Exception(f"思维导图生成失败: {result.stderr}")
        
        socketio.emit('progress', {
            'task_id': task_id,
            'stage': 'packaging',
            'message': '正在打包结果文件...',
            'progress': 90
        })
        
        # 创建结果包
        result_info = create_result_package(transcript_dir, task_id)
        
        # 清理临时文件
        for path in [filepath, target_path]:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except:
                pass
        
        # 发送完成消息
        socketio.emit('progress', {
            'task_id': task_id,
            'stage': 'complete',
            'message': '处理完成！',
            'progress': 100,
            'result': result_info
        })
        
    except Exception as e:
        socketio.emit('progress', {
            'task_id': task_id,
            'stage': 'error',
            'message': f'处理失败：{str(e)}',
            'progress': -1
        })
        
        # 清理文件
        for path in [filepath, target_path]:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except:
                pass

def create_result_package(transcript_dir, task_id):
    """创建结果文件包"""
    try:
        result_dir = f"results_{task_id}"
        os.makedirs(result_dir, exist_ok=True)
        
        # 复制转写结果
        if os.path.exists(transcript_dir):
            shutil.copytree(transcript_dir, os.path.join(result_dir, 'transcripts'), dirs_exist_ok=True)
        
        # 复制思维导图
        mindmap_path = "output/mindmap.html"
        if os.path.exists(mindmap_path):
            shutil.copy2(mindmap_path, os.path.join(result_dir, 'mindmap.html'))
        
        # 创建ZIP包
        zip_filename = f"results_{task_id}.zip"
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(result_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, result_dir)
                    zipf.write(file_path, arcname)
        
        # 读取汇总信息
        summary_path = os.path.join(transcript_dir, 'summary.txt')
        summary_content = ""
        if os.path.exists(summary_path):
            with open(summary_path, 'r', encoding='utf-8') as f:
                summary_content = f.read()
        
        # 清理临时目录
        shutil.rmtree(result_dir)
        
        return {
            'transcript_dir': transcript_dir,
            'zip_file': zip_filename,
            'mindmap_available': os.path.exists(mindmap_path),
            'summary': summary_content[:500] + "..." if len(summary_content) > 500 else summary_content
        }
        
    except Exception as e:
        print(f"创建结果包失败：{e}")
        return None

@app.route('/download/<path:filename>')
def download_file(filename):
    """下载文件"""
    try:
        if os.path.exists(filename):
            return send_file(filename, as_attachment=True)
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': f'下载失败：{str(e)}'}), 500

@app.route('/view_mindmap/<task_id>')
def view_mindmap(task_id):
    """查看思维导图"""
    mindmap_path = "output/mindmap.html"
    if os.path.exists(mindmap_path):
        return send_file(mindmap_path)
    else:
        return "思维导图文件不存在", 404

@app.route('/api/status')
def api_status():
    """API状态检查"""
    return jsonify({
        'status': 'running',
        'supported_formats': SUPPORTED_FORMATS,
        'max_file_size': f'{MAX_FILE_SIZE}MB',
        'local_model_available': LOCAL_MODEL_AVAILABLE,
        'use_local_model': audio_processor.use_local_model,
        'whisper_model_size': WHISPER_MODEL_SIZE,
        'min_speakers': MIN_SPEAKERS,
        'max_speakers': MAX_SPEAKERS
    })

@app.route('/api/process', methods=['POST'])
def api_process():
    """API接口：直接处理音频文件"""
    try:
        data = request.get_json()
        audio_file = data.get('audio_file')
        
        if not audio_file or not os.path.exists(audio_file):
            return jsonify({'error': '音频文件不存在'}), 400
        
        # 运行完整处理流程
        processor = AudioProcessor()
        success = processor.run_full_pipeline(audio_file)
        
        if success:
            # 查找结果
            transcript_dir = processor.find_latest_transcript_dir()
            mindmap_file = "output/mindmap.html"
            
            return jsonify({
                'success': True,
                'transcript_dir': transcript_dir,
                'mindmap_file': mindmap_file if os.path.exists(mindmap_file) else None,
                'summary_file': os.path.join(transcript_dir, 'summary.txt') if transcript_dir else None
            })
        else:
            return jsonify({'error': '处理失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'API处理失败：{str(e)}'}), 500

@socketio.on('connect')
def handle_connect():
    print('客户端已连接')

@socketio.on('disconnect')
def handle_disconnect():
    print('客户端已断开')

def run_full_pipeline_command_line(audio_file=None, transcript_dir=None, audio_only=False, graph_only=False):
    """命令行模式的完整流程"""
    processor = AudioProcessor()
    
    if audio_only:
        # 仅处理音频
        return processor.process_audio(audio_file)
    elif graph_only:
        # 仅生成思维导图
        return processor.generate_mindmap(transcript_dir)
    else:
        # 完整流程
        return processor.run_full_pipeline(audio_file, transcript_dir)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='音频转文字Web应用 - 一体化版本')
    parser.add_argument('--web', action='store_true', help='启动Web服务器')
    parser.add_argument('--audio', '-a', help='指定音频文件路径')
    parser.add_argument('--transcript', '-t', help='指定现有转写目录路径')
    parser.add_argument('--audio-only', action='store_true', help='仅处理音频，不生成思维导图')
    parser.add_argument('--graph-only', action='store_true', help='仅生成思维导图，不处理音频')
    parser.add_argument('--port', type=int, default=5000, help='Web服务器端口 (默认: 5000)')
    parser.add_argument('--host', default='0.0.0.0', help='Web服务器主机 (默认: 0.0.0.0)')
    
    args = parser.parse_args()
    
    if args.web or (not args.audio and not args.transcript and not args.audio_only and not args.graph_only):
        # 启动Web服务器
        print("🌐 启动音频转文字Web应用...")
        print(f"📱 访问地址: http://localhost:{args.port}")
        print("📁 支持格式:", ", ".join(SUPPORTED_FORMATS))
        print(f"💾 最大文件大小: {MAX_FILE_SIZE}MB")
        print(f"🏠 本地模型: {'可用' if LOCAL_MODEL_AVAILABLE else '不可用'}")
        print(f"🎤 Whisper模型: {WHISPER_MODEL_SIZE}")
        print(f"👥 说话人数量: {MIN_SPEAKERS}-{MAX_SPEAKERS}")
        print("=" * 50)
        
        socketio.run(app, host=args.host, port=args.port, debug=False)
    else:
        # 命令行模式
        success = run_full_pipeline_command_line(
            args.audio, 
            args.transcript, 
            args.audio_only, 
            args.graph_only
        )
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
