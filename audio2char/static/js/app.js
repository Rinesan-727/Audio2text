// 音频转文字Web应用前端JavaScript

class AudioProcessor {
    constructor() {
        this.socket = io();
        this.currentTaskId = null;
        this.selectedFile = null;
        
        this.initializeElements();
        this.bindEvents();
        this.initializeSocket();
    }
    
    initializeElements() {
        // 获取DOM元素
        this.uploadArea = document.getElementById('uploadArea');
        this.audioFile = document.getElementById('audioFile');
        this.selectFileLink = document.getElementById('selectFile');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.fileInfo = document.getElementById('fileInfo');
        this.fileName = document.getElementById('fileName');
        this.fileSize = document.getElementById('fileSize');
        this.progressArea = document.getElementById('progressArea');
        this.progressBar = document.getElementById('progressBar');
        this.progressMessage = document.getElementById('progressMessage');
        this.resultArea = document.getElementById('resultArea');
        this.emptyState = document.getElementById('emptyState');
        this.viewMindmapBtn = document.getElementById('viewMindmapBtn');
        this.downloadResultBtn = document.getElementById('downloadResultBtn');
        this.summaryPreview = document.getElementById('summaryPreview');
        this.mindmapModal = new bootstrap.Modal(document.getElementById('mindmapModal'));
        this.mindmapFrame = document.getElementById('mindmapFrame');
    }
    
    bindEvents() {
        // 文件选择事件
        this.selectFileLink.addEventListener('click', (e) => {
            e.preventDefault();
            this.audioFile.click();
        });
        
        this.audioFile.addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files[0]);
        });
        
        // 拖拽上传事件
        this.uploadArea.addEventListener('click', () => {
            this.audioFile.click();
        });
        
        this.uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.uploadArea.classList.add('dragover');
        });
        
        this.uploadArea.addEventListener('dragleave', () => {
            this.uploadArea.classList.remove('dragover');
        });
        
        this.uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        });
        
        // 上传按钮事件
        this.uploadBtn.addEventListener('click', () => {
            this.uploadFile();
        });
        
        // 查看思维导图按钮
        this.viewMindmapBtn.addEventListener('click', () => {
            this.viewMindmap();
        });
        
        // 下载结果按钮
        this.downloadResultBtn.addEventListener('click', () => {
            this.downloadResult();
        });
    }
    
    initializeSocket() {
        // Socket.IO事件监听
        this.socket.on('connect', () => {
            console.log('已连接到服务器');
        });
        
        this.socket.on('disconnect', () => {
            console.log('与服务器断开连接');
        });
        
        this.socket.on('progress', (data) => {
            this.handleProgress(data);
        });
    }
    
    handleFileSelect(file) {
        if (!file) return;
        
        // 检查文件类型
        const allowedTypes = ['audio/wav', 'audio/mpeg', 'audio/mp4', 'audio/flac', 'audio/aac', 'audio/ogg'];
        const allowedExtensions = ['.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg'];
        
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
            this.showAlert('不支持的文件格式。请选择 WAV, MP3, M4A, FLAC, AAC 或 OGG 格式的音频文件。', 'danger');
            return;
        }
        
        // 检查文件大小 (500MB)
        const maxSize = 500 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showAlert('文件太大。最大支持 500MB 的音频文件。', 'danger');
            return;
        }
        
        this.selectedFile = file;
        
        // 显示文件信息
        this.fileName.textContent = file.name;
        this.fileSize.textContent = this.formatFileSize(file.size);
        this.fileInfo.style.display = 'block';
        
        // 启用上传按钮
        this.uploadBtn.disabled = false;
        
        // 更新上传区域样式
        this.uploadArea.classList.add('success');
    }
    
    uploadFile() {
        if (!this.selectedFile) {
            this.showAlert('请先选择音频文件', 'warning');
            return;
        }
        
        const formData = new FormData();
        formData.append('audio', this.selectedFile);
        
        // 禁用上传按钮
        this.uploadBtn.disabled = true;
        this.uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>上传中...';
        
        // 显示进度区域
        this.showProgressArea();
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.currentTaskId = data.task_id;
                this.updateProgress(10, '文件上传成功，开始处理...');
                this.updateStage('upload', 'completed');
            } else {
                throw new Error(data.error || '上传失败');
            }
        })
        .catch(error => {
            this.showAlert(`上传失败: ${error.message}`, 'danger');
            this.resetUploadState();
        });
    }
    
    handleProgress(data) {
        if (data.task_id !== this.currentTaskId) return;
        
        if (data.stage === 'error') {
            this.showAlert(`处理失败: ${data.message}`, 'danger');
            this.resetUploadState();
            return;
        }
        
        // 更新进度条
        if (data.progress >= 0) {
            this.updateProgress(data.progress, data.message);
        }
        
        // 更新阶段指示器
        switch (data.stage) {
            case 'start':
                this.updateStage('upload', 'active');
                break;
            case 'transcription':
            case 'diarization':
            case 'recognition':
                this.updateStage('upload', 'completed');
                this.updateStage('transcription', 'active');
                break;
            case 'mindmap':
                this.updateStage('transcription', 'completed');
                this.updateStage('mindmap', 'active');
                break;
            case 'complete':
                this.updateStage('mindmap', 'completed');
                this.updateStage('complete', 'completed');
                if (data.result) {
                    this.showResult(data.result);
                }
                break;
        }
    }
    
    updateProgress(percentage, message) {
        this.progressBar.style.width = `${percentage}%`;
        this.progressBar.setAttribute('aria-valuenow', percentage);
        this.progressMessage.textContent = message;
        
        if (percentage >= 100) {
            this.progressBar.classList.remove('progress-bar-animated');
        }
    }
    
    updateStage(stageName, status) {
        const stageElement = document.getElementById(`stage-${stageName}`);
        if (stageElement) {
            stageElement.classList.remove('active', 'completed');
            if (status) {
                stageElement.classList.add(status);
            }
        }
    }
    
    showProgressArea() {
        this.emptyState.style.display = 'none';
        this.resultArea.style.display = 'none';
        this.progressArea.style.display = 'block';
        
        // 重置进度
        this.updateProgress(0, '准备处理...');
        
        // 重置阶段指示器
        const stages = ['upload', 'transcription', 'mindmap', 'complete'];
        stages.forEach(stage => {
            this.updateStage(stage, '');
        });
    }
    
    showResult(result) {
        this.progressArea.style.display = 'none';
        this.resultArea.style.display = 'block';
        
        // 保存结果数据
        this.resultData = result;
        
        // 显示摘要预览
        if (result.summary) {
            this.summaryPreview.textContent = result.summary;
        }
        
        // 重置上传状态
        this.resetUploadState();
    }
    
    resetUploadState() {
        this.uploadBtn.disabled = false;
        this.uploadBtn.innerHTML = '<i class="bi bi-upload me-2"></i>开始处理';
        this.selectedFile = null;
        this.currentTaskId = null;
        
        // 重置文件选择
        this.audioFile.value = '';
        this.fileInfo.style.display = 'none';
        this.uploadArea.classList.remove('success', 'error');
    }
    
    viewMindmap() {
        if (this.currentTaskId) {
            this.mindmapFrame.src = `/view_mindmap/${this.currentTaskId}`;
            this.mindmapModal.show();
        }
    }
    
    downloadResult() {
        if (this.resultData && this.resultData.zip_file) {
            window.open(`/download/${this.resultData.zip_file}`, '_blank');
        }
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    showAlert(message, type = 'info') {
        // 创建警告框
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // 插入到页面顶部
        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        // 5秒后自动消失
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new AudioProcessor();
});

// 防止页面意外刷新时丢失上传
window.addEventListener('beforeunload', (e) => {
    if (document.getElementById('progressArea').style.display !== 'none') {
        e.preventDefault();
        e.returnValue = '正在处理音频文件，确定要离开吗？';
    }
});
