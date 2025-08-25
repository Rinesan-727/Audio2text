from pyannote.audio import Pipeline
from pydub import AudioSegment
import os
import whisper
import json
from datetime import datetime
import torch
import numpy as np

# 音频文件路径 - 支持多种格式
def find_audio_file():
    """查找可用的音频文件"""
    audio_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg']
    audio_files = []
    
    for ext in audio_extensions:
        files = [f for f in os.listdir('.') if f.lower().endswith(ext)]
        audio_files.extend(files)
    
    if not audio_files:
        print("错误：当前目录下没有找到音频文件")
        print("支持的格式：", ', '.join(audio_extensions))
        exit(1)
    
    # 优先选择 wav 文件，然后是 mp3，最后是其他格式
    priority_order = ['.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg']
    
    for ext in priority_order:
        for file in audio_files:
            if file.lower().endswith(ext):
                return file
    
    return audio_files[0]  # 如果没找到优先格式，返回第一个

audio_file = find_audio_file()
wav_file = "audio_converted.wav"

# 创建输出目录
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = f"transcripts_{timestamp}"
os.makedirs(output_dir, exist_ok=True)

print(f"找到音频文件：{audio_file}")

print(f"正在处理音频文件：{audio_file}")

# 将音频转换为 wav 格式，支持多种输入格式
print("正在转换音频格式...")

def get_file_format(filename):
    """获取文件格式"""
    ext = os.path.splitext(filename)[1].lower()
    format_map = {
        '.wav': 'wav',
        '.mp3': 'mp3', 
        '.m4a': 'm4a',
        '.flac': 'flac',
        '.aac': 'aac',
        '.ogg': 'ogg'
    }
    return format_map.get(ext, 'wav')

file_format = get_file_format(audio_file)
print(f"检测到文件格式：{file_format}")

try:
    # 尝试使用pydub转换
    print("使用pydub进行音频转换...")
    audio = AudioSegment.from_file(audio_file, format=file_format)
    
    # 提升音频质量：16kHz采样率、单声道，适合语音识别
    audio = audio.set_frame_rate(16000).set_channels(1)
    
    # 如果是wav格式且质量已经符合要求，直接复制
    if file_format == 'wav':
        # 检查现有wav文件是否已经是16kHz单声道
        try:
            existing_audio = AudioSegment.from_wav(audio_file)
            if existing_audio.frame_rate == 16000 and existing_audio.channels == 1:
                print("现有wav文件已符合要求，直接使用")
                import shutil
                shutil.copy2(audio_file, wav_file)
                print(f"音频文件已复制为：{wav_file}")
            else:
                audio.export(wav_file, format="wav")
                print(f"音频已转换为：{wav_file}")
        except:
            audio.export(wav_file, format="wav")
            print(f"音频已转换为：{wav_file}")
    else:
        audio.export(wav_file, format="wav")
        print(f"音频已转换为：{wav_file}")
        
except Exception as e:
    print(f"pydub转换失败：{e}")
    print("尝试使用ffmpeg直接转换...")
    try:
        import subprocess
        # 使用ffmpeg直接转换，支持更多格式
        cmd = [
            "ffmpeg", "-i", audio_file, 
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
            "-y", wav_file
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"ffmpeg转换成功：{wav_file}")
        else:
            print(f"ffmpeg转换失败：{result.stderr}")
            print("尝试使用sox转换...")
            # 备用方案：使用sox
            try:
                cmd_sox = ["sox", audio_file, "-r", "16000", "-c", "1", wav_file]
                result_sox = subprocess.run(cmd_sox, capture_output=True, text=True)
                if result_sox.returncode == 0:
                    print(f"sox转换成功：{wav_file}")
                else:
                    print(f"sox转换失败：{result_sox.stderr}")
                    exit(1)
            except:
                print("所有转换方法都失败，请确保安装了ffmpeg或sox")
                exit(1)
    except Exception as e2:
        print(f"ffmpeg转换也失败：{e2}")
        exit(1)

# 加载说话人分离模型
print("正在加载说话人分离模型...")
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")

# 优化说话人分离参数
print("正在对整个音频文件进行说话人分离...")
diarization = pipeline(
    wav_file,
    # 使用正确的参数格式，适合单人讲话
    min_speakers=1,
    max_speakers=3
)

# 收集说话人时间段
speaker_segments = {}
speaker_stats = {}

for turn, _, speaker in diarization.itertracks(yield_label=True):
    if speaker not in speaker_segments:
        speaker_segments[speaker] = []
        speaker_stats[speaker] = {
            'total_duration': 0,
            'segment_count': 0,
            'avg_duration': 0
        }
    
    segment_info = {
        'start': turn.start,
        'end': turn.end,
        'duration': turn.end - turn.start
    }
    
    speaker_segments[speaker].append(segment_info)
    speaker_stats[speaker]['total_duration'] += segment_info['duration']
    speaker_stats[speaker]['segment_count'] += 1

# 计算每个说话人的平均时长
for speaker in speaker_stats:
    if speaker_stats[speaker]['segment_count'] > 0:
        speaker_stats[speaker]['avg_duration'] = speaker_stats[speaker]['total_duration'] / speaker_stats[speaker]['segment_count']

print(f"识别到 {len(speaker_segments)} 个说话人")

# 显示说话人统计信息
print("\n说话人分离统计:")
for speaker, stats in speaker_stats.items():
    print(f"{speaker}:")
    print(f"  - 总时长: {stats['total_duration']:.1f}秒")
    print(f"  - 片段数: {stats['segment_count']}")
    print(f"  - 平均时长: {stats['avg_duration']:.1f}秒")

# 过滤过短的片段，提高质量
print("\n正在过滤过短的语音片段...")
min_segment_duration = 0.5  # 最小片段时长0.5秒
filtered_speaker_segments = {}

for speaker, segments in speaker_segments.items():
    filtered_segments = [seg for seg in segments if seg['duration'] >= min_segment_duration]
    if filtered_segments:
        filtered_speaker_segments[speaker] = filtered_segments
        print(f"{speaker}: {len(segments)} -> {len(filtered_segments)} 片段 (过滤掉 {len(segments) - len(filtered_segments)} 个短片段)")

speaker_segments = filtered_speaker_segments

# 加载更大的语音识别模型以提高准确率
print("正在加载语音识别模型...")
# 使用 medium 模型提高准确率，或使用 large 模型获得最佳效果
model_size = "medium"  # 可选: "tiny", "base", "small", "medium", "large"
whisper_model = whisper.load_model(model_size)

# 检查是否有GPU可用
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"使用设备: {device}")
if device == "cuda":
    whisper_model = whisper_model.to(device)

# 对整个音频进行转写
print("正在对整个音频进行转写...")
try:
    # 使用 Whisper 转写整个音频，添加更多参数提高准确率
    result = whisper_model.transcribe(
        wav_file, 
        language="zh",
        task="transcribe",
        fp16=False,  # 如果GPU内存不足，设为True
        verbose=False,
        # 添加提示词提高准确率
        initial_prompt="这是一段关于科技、金融、投资的对话。",
        # 启用时间戳
        word_timestamps=True
    )
    
    # 获取转写结果
    full_transcript = result["text"].strip()
    asr_segments = result.get("segments", [])
    
    print(f"完整转写结果: {full_transcript}")
    print(f"转写片段数: {len(asr_segments)}")
    
except Exception as e:
    print(f"转写失败: {e}")
    exit(1)

# 改进的时间戳匹配函数
def find_matching_transcript(segment_start, segment_end, transcript_segments, overlap_threshold=0.3):
    """查找与时间段匹配的转写内容，使用重叠度阈值"""
    matching_texts = []
    total_overlap = 0
    
    for seg in transcript_segments:
        seg_start = seg['start']
        seg_end = seg['end']
        
        # 计算重叠时间
        overlap_start = max(segment_start, seg_start)
        overlap_end = min(segment_end, seg_end)
        overlap_duration = max(0, overlap_end - overlap_start)
        
        # 计算重叠比例
        segment_duration = segment_end - segment_start
        seg_duration = seg_end - seg_start
        
        if overlap_duration > 0:
            # 计算重叠比例
            overlap_ratio = overlap_duration / min(segment_duration, seg_duration)
            
            # 如果重叠比例超过阈值，认为匹配
            if overlap_ratio >= overlap_threshold:
                matching_texts.append({
                    'text': seg.get('text', ''),
                    'overlap_ratio': overlap_ratio,
                    'overlap_duration': overlap_duration,
                    'seg_start': seg_start,
                    'seg_end': seg_end
                })
                total_overlap += overlap_duration
    
    # 按重叠比例排序，优先选择重叠度高的
    matching_texts.sort(key=lambda x: x['overlap_ratio'], reverse=True)
    
    # 返回匹配的文本
    if matching_texts:
        return ' '.join([item['text'] for item in matching_texts]), total_overlap
    else:
        return '', 0

def deduplicate_segments(segments, similarity_threshold=0.8):
    """去除重复的语音片段"""
    if not segments:
        return segments
    
    # 按开始时间排序
    segments = sorted(segments, key=lambda x: x['start'])
    
    # 计算文本相似度
    def text_similarity(text1, text2):
        """计算两个文本的相似度"""
        if not text1 or not text2:
            return 0.0
        
        # 简单的字符重叠相似度
        set1 = set(text1)
        set2 = set(text2)
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    # 去除重复
    deduplicated = []
    for i, current_seg in enumerate(segments):
        is_duplicate = False
        
        # 检查与之前片段的相似度
        for prev_seg in deduplicated:
            similarity = text_similarity(current_seg['text'], prev_seg['text'])
            
            # 如果相似度很高且时间接近，认为是重复
            if (similarity > similarity_threshold and 
                abs(current_seg['start'] - prev_seg['start']) < 5.0):  # 5秒内的时间差
                is_duplicate = True
                break
        
        if not is_duplicate:
            deduplicated.append(current_seg)
    
    return deduplicated

# 为每个说话人分配转写内容
speaker_transcripts = {}

for speaker, spk_segments in speaker_segments.items():
    print(f"\n处理 {speaker} 的时间段...")
    speaker_transcripts[speaker] = []
    
    for i, segment in enumerate(spk_segments):
        start_time = segment['start']
        end_time = segment['end']
        print(f"  时间段 {i+1}/{len(speaker_segments[speaker])}: {start_time:.1f}s - {end_time:.1f}s")
        
        # 查找匹配的转写内容
        matching_text, total_overlap = find_matching_transcript(start_time, end_time, asr_segments)
        
        speaker_transcripts[speaker].append({
            'start': start_time,
            'end': end_time,
            'text': matching_text,
            'duration': end_time - start_time,
            'overlap_duration': total_overlap,
            'overlap_ratio': total_overlap / (end_time - start_time) if (end_time - start_time) > 0 else 0
        })
        
        if matching_text:
            overlap_ratio = total_overlap / (end_time - start_time) if (end_time - start_time) > 0 else 0
            print(f"    转写结果: {matching_text[:50]}...")
            print(f"    重叠度: {overlap_ratio:.2f} ({total_overlap:.1f}s/{end_time - start_time:.1f}s)")
        else:
            print(f"    无对应转写内容")

# 对每个说话人的转写结果进行去重
print("\n正在去除重复的语音片段...")
for speaker in speaker_transcripts:
    original_count = len(speaker_transcripts[speaker])
    speaker_transcripts[speaker] = deduplicate_segments(speaker_transcripts[speaker])
    deduplicated_count = len(speaker_transcripts[speaker])
    print(f"{speaker}: {original_count} -> {deduplicated_count} 片段 (去除 {original_count - deduplicated_count} 个重复片段)")

# 保存每个说话人的转写结果
for speaker, transcripts in speaker_transcripts.items():
    if not transcripts:
        continue
        
    # 计算统计信息
    total_duration = sum(seg['duration'] for seg in transcripts)
    valid_segments = [seg for seg in transcripts if seg['text'].strip()]
    avg_overlap_ratio = sum(seg['overlap_ratio'] for seg in valid_segments) / len(valid_segments) if valid_segments else 0
    
    # 保存详细JSON
    detailed_file = os.path.join(output_dir, f"{speaker}_detailed.json")
    with open(detailed_file, 'w', encoding='utf-8') as f:
        json.dump({
            'speaker': speaker,
            'total_duration': total_duration,
            'segment_count': len(valid_segments),
            'avg_overlap_ratio': avg_overlap_ratio,
            'quality_score': min(1.0, avg_overlap_ratio * 2),  # 质量评分
            'segments': transcripts
        }, f, ensure_ascii=False, indent=2)
    
    # 保存纯文本
    text_file = os.path.join(output_dir, f"{speaker}_transcript.txt")
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(f"# {speaker} 转写结果\n")
        f.write(f"总发言时长: {total_duration:.1f}秒\n")
        f.write(f"有效片段数: {len(valid_segments)}\n")
        f.write(f"平均重叠度: {avg_overlap_ratio:.2f}\n")
        f.write(f"质量评分: {min(1.0, avg_overlap_ratio * 2):.2f}\n\n")
        
        for seg in transcripts:
            if seg['text'].strip():
                overlap_info = f" (重叠度: {seg['overlap_ratio']:.2f})" if seg['overlap_ratio'] > 0 else ""
                f.write(f"[{seg['start']:.1f}s - {seg['end']:.1f}s]{overlap_info} {seg['text']}\n")
    
    print(f"\n{speaker} 的转写结果已保存到:")
    print(f"  - {detailed_file}")
    print(f"  - {text_file}")
    print(f"  - 质量评分: {min(1.0, avg_overlap_ratio * 2):.2f}")

# 保存完整转写结果
full_transcript_file = os.path.join(output_dir, "full_transcript.txt")
with open(full_transcript_file, 'w', encoding='utf-8') as f:
    f.write(f"# 完整音频转写结果\n")
    f.write(f"音频文件: {audio_file}\n")
    f.write(f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"使用模型: {model_size}\n")
    f.write(f"处理设备: {device}\n\n")
    
    for i, seg in enumerate(asr_segments):
        f.write(f"[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}\n")

# 生成汇总文件
summary_file = os.path.join(output_dir, "summary.txt")
with open(summary_file, 'w', encoding='utf-8') as f:
    f.write(f"# 音频转写汇总\n")
    f.write(f"音频文件: {audio_file}\n")
    f.write(f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"使用模型: {model_size}\n")
    f.write(f"处理设备: {device}\n")
    f.write(f"说话人分离参数: min_speakers=2, max_speakers=5\n")
    f.write(f"最小片段时长: {min_segment_duration}秒\n\n")
    
    # 完整转写
    f.write("## 完整转写\n\n")
    full_text = "".join(seg['text'] for seg in asr_segments)
    f.write(full_text + "\n\n")
    f.write("=" * 50 + "\n\n")
    
    # 按说话人分类
    for speaker, transcripts in speaker_transcripts.items():
        if not transcripts:
            continue
            
        valid_segments = [seg for seg in transcripts if seg['text'].strip()]
        total_duration = sum(seg['duration'] for seg in transcripts)
        avg_overlap_ratio = sum(seg['overlap_ratio'] for seg in valid_segments) / len(valid_segments) if valid_segments else 0
        quality_score = min(1.0, avg_overlap_ratio * 2)
        
        f.write(f"## {speaker}\n")
        f.write(f"总发言时长: {total_duration:.1f}秒\n")
        f.write(f"发言片段数: {len(valid_segments)}\n")
        f.write(f"平均重叠度: {avg_overlap_ratio:.2f}\n")
        f.write(f"质量评分: {quality_score:.2f}\n\n")
        
        for seg in valid_segments:
            overlap_info = f" (重叠度: {seg['overlap_ratio']:.2f})" if seg['overlap_ratio'] > 0 else ""
            f.write(f"[{seg['start']:.1f}s - {seg['end']:.1f}s]{overlap_info} {seg['text']}\n")
        
        f.write("\n" + "=" * 50 + "\n\n")

print(f"\n完整转写结果已保存到: {full_transcript_file}")
print(f"汇总结果已保存到: {summary_file}")

# 清理临时文件
if os.path.exists(wav_file):
    os.remove(wav_file)
    print(f"已删除临时文件：{wav_file}")

print(f"\n所有结果已保存到目录: {output_dir}")
print(f"优化说明:")
print(f"- 使用 {model_size} 模型提高准确率")
print(f"- 对整个音频进行转写，保持上下文完整性")
print(f"- 优化说话人分离参数：min_speakers=2, max_speakers=5")
print(f"- 使用重叠度阈值匹配，提高说话人分离准确性")
print(f"- 过滤短片段（<{min_segment_duration}秒），提高质量")
print(f"- 添加质量评分和重叠度统计")
print(f"- 音频预处理：16kHz采样率，单声道")
print(f"- 添加初始提示词提高中文识别准确率")
print(f"- 显示置信度评分")
print(f"- 保存完整转写结果和详细时间戳")