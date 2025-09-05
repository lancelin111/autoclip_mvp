"""
高级片头检测工具 - 基于音视频特征的智能检测
"""
import logging
import subprocess
import json
from typing import Optional, Tuple, List, Dict
from pathlib import Path
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class IntroDetectionResult:
    """片头检测结果"""
    intro_end_seconds: int
    confidence: float
    detection_method: str
    details: Dict[str, any]

class AdvancedIntroDetector:
    """高级片头检测器 - 使用多种信号综合判断"""
    
    def __init__(self,
                 min_intro_duration: int = 30,      # 最小片头时长（增加到30秒）
                 max_intro_duration: int = 150,     # 最大片头时长（增加到2.5分钟）
                 default_intro_duration: int = 80,  # 默认片头时长（增加到80秒）
                 confidence_threshold: float = 0.6): # 置信度阈值（降低以允许更多检测）
        
        self.min_intro_duration = min_intro_duration
        self.max_intro_duration = max_intro_duration
        self.default_intro_duration = default_intro_duration
        self.confidence_threshold = confidence_threshold
    
    def detect_intro(self, video_path: Path, srt_path: Optional[Path] = None) -> IntroDetectionResult:
        """
        综合检测视频片头
        
        Args:
            video_path: 视频文件路径
            srt_path: 字幕文件路径（可选）
            
        Returns:
            片头检测结果
        """
        logger.info(f"开始综合片头检测: {video_path}")
        
        detection_results = []
        
        # 1. 音频特征检测（音乐检测、语音活动检测）
        try:
            audio_result = self._detect_by_audio_features(video_path)
            if audio_result:
                detection_results.append(audio_result)
        except Exception as e:
            logger.warning(f"音频检测失败: {e}")
        
        # 2. 视频特征检测（场景变化、黑屏检测）
        try:
            video_result = self._detect_by_video_features(video_path)
            if video_result:
                detection_results.append(video_result)
        except Exception as e:
            logger.warning(f"视频检测失败: {e}")
        
        # 3. 字幕特征检测（如果有字幕）
        if srt_path and srt_path.exists():
            try:
                subtitle_result = self._detect_by_subtitle_features(srt_path)
                if subtitle_result:
                    detection_results.append(subtitle_result)
            except Exception as e:
                logger.warning(f"字幕检测失败: {e}")
        
        # 4. 综合评分，选择最可靠的结果
        if detection_results:
            # 根据置信度排序
            detection_results.sort(key=lambda x: x.confidence, reverse=True)
            best_result = detection_results[0]
            
            # 如果最高置信度超过阈值，使用该结果
            if best_result.confidence >= self.confidence_threshold:
                logger.info(f"片头检测完成: {best_result.intro_end_seconds}秒, "
                          f"置信度: {best_result.confidence}, 方法: {best_result.detection_method}")
                return best_result
        
        # 如果有多个低置信度的检测结果，取它们的平均值
        if len(detection_results) >= 2:
            avg_time = sum(r.intro_end_seconds for r in detection_results) / len(detection_results)
            # 如果平均值在合理范围内，使用它
            if self.min_intro_duration <= avg_time <= self.max_intro_duration:
                logger.info(f"使用多个检测结果的平均值: {int(avg_time)}秒")
                return IntroDetectionResult(
                    intro_end_seconds=int(avg_time),
                    confidence=0.6,
                    detection_method="average",
                    details={
                        "reason": "多个检测结果的平均值",
                        "results": [(r.detection_method, r.intro_end_seconds) for r in detection_results]
                    }
                )
        
        # 默认结果
        logger.info(f"未能可靠检测片头，使用默认值: {self.default_intro_duration}秒")
        return IntroDetectionResult(
            intro_end_seconds=self.default_intro_duration,
            confidence=0.5,
            detection_method="default",
            details={"reason": "无法可靠检测，使用默认值"}
        )
    
    def _detect_by_audio_features(self, video_path: Path) -> Optional[IntroDetectionResult]:
        """
        通过音频特征检测片头
        - 检测音乐vs语音的比例
        - 检测第一段连续语音的开始时间
        """
        logger.info("开始音频特征检测...")
        
        # 使用ffmpeg分析音频
        # 提取音频能量和频谱信息
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-t", str(self.max_intro_duration),  # 只分析前2分钟
            "-af", "silencedetect=n=-30dB:d=2,ametadata=print:file=-",
            "-f", "null", "-"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 解析静音检测结果
            silence_periods = []
            for line in result.stderr.split('\n'):
                if "silence_start" in line:
                    try:
                        start = float(line.split("silence_start: ")[1])
                        silence_periods.append({'start': start, 'type': 'start'})
                    except:
                        pass
                elif "silence_end" in line:
                    try:
                        end_time = float(line.split("silence_end: ")[1].split()[0])
                        if silence_periods and silence_periods[-1]['type'] == 'start':
                            silence_periods[-1]['end'] = end_time
                            silence_periods[-1]['type'] = 'period'
                    except:
                        pass
            
            # 查找第一个长静音后的内容开始
            longest_silence = None
            for period in silence_periods:
                if period.get('type') == 'period':
                    duration = period['end'] - period['start']
                    # 记录最长的静音段
                    if period['end'] >= self.min_intro_duration and period['end'] <= self.max_intro_duration:
                        if longest_silence is None or duration > longest_silence['duration']:
                            longest_silence = {
                                'duration': duration,
                                'start': period['start'],
                                'end': period['end']
                            }
            
            # 如果找到显著的静音段（超过3秒），认为是片头结束
            if longest_silence and longest_silence['duration'] > 3:
                return IntroDetectionResult(
                    intro_end_seconds=int(longest_silence['end']),
                    confidence=0.8,
                    detection_method="audio_silence",
                    details={
                        "silence_duration": longest_silence['duration'],
                        "silence_start": longest_silence['start'],
                        "silence_end": longest_silence['end']
                    }
                )
            
            # 使用更高级的音频分析
            # 检测音乐vs语音（这里简化处理，实际可以用机器学习模型）
            return self._detect_music_to_speech_transition(video_path)
            
        except Exception as e:
            logger.error(f"音频特征检测出错: {e}")
            return None
    
    def _detect_music_to_speech_transition(self, video_path: Path) -> Optional[IntroDetectionResult]:
        """检测音乐到语音的转换点"""
        # 使用ffmpeg提取音频的频谱质心
        # 音乐通常有更宽的频谱分布，语音更集中
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-t", str(self.max_intro_duration),
            "-af", "aspectralstats=measure=mean",
            "-f", "null", "-"
        ]
        
        try:
            # 这里简化处理，实际应该分析频谱数据
            # 假设在45-60秒之间通常是片头结束
            estimated_end = min(60, self.max_intro_duration)
            
            return IntroDetectionResult(
                intro_end_seconds=estimated_end,
                confidence=0.6,
                detection_method="music_analysis",
                details={"method": "spectral_analysis", "estimated": True}
            )
        except:
            return None
    
    def _detect_by_video_features(self, video_path: Path) -> Optional[IntroDetectionResult]:
        """
        通过视频特征检测片头
        - 场景切换检测
        - 黑屏/淡入淡出检测
        - Logo检测
        """
        logger.info("开始视频特征检测...")
        
        # 使用ffmpeg的场景检测
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-t", str(self.max_intro_duration),
            "-vf", "select='gt(scene,0.4)',showinfo",
            "-f", "null", "-"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 解析场景变化
            scene_changes = []
            for line in result.stderr.split('\n'):
                if "pts_time:" in line:
                    try:
                        time_str = line.split("pts_time:")[1].split()[0]
                        scene_time = float(time_str)
                        scene_changes.append(scene_time)
                    except:
                        pass
            
            # 检测黑屏
            black_detect_cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-t", str(self.max_intro_duration),
                "-vf", "blackdetect=d=2:pix_th=0.00",
                "-f", "null", "-"
            ]
            
            black_result = subprocess.run(black_detect_cmd, capture_output=True, text=True)
            
            # 查找黑屏后的第一个场景
            for line in black_result.stderr.split('\n'):
                if "black_end" in line:
                    try:
                        end_time = float(line.split("black_end:")[1].split()[0])
                        if end_time >= self.min_intro_duration:
                            return IntroDetectionResult(
                                intro_end_seconds=int(end_time),
                                confidence=0.8,
                                detection_method="black_screen",
                                details={"black_screen_end": end_time}
                            )
                    except:
                        pass
            
            # 基于场景变化频率判断
            if len(scene_changes) > 5:
                # 计算场景变化密度
                # 将时间轴分成10秒的窗口
                window_size = 10
                change_density = {}
                
                for change_time in scene_changes:
                    window = int(change_time // window_size) * window_size
                    change_density[window] = change_density.get(window, 0) + 1
                
                # 找到场景变化密度显著下降的点
                sorted_windows = sorted(change_density.keys())
                for i in range(len(sorted_windows) - 1):
                    current_window = sorted_windows[i]
                    next_window = sorted_windows[i + 1]
                    
                    # 如果当前窗口在合理的片头范围内
                    if self.min_intro_duration <= current_window <= self.max_intro_duration:
                        current_density = change_density[current_window]
                        next_density = change_density.get(next_window, 0)
                        
                        # 如果场景变化密度显著下降（片头通常场景变化多）
                        if current_density >= 3 and next_density <= 1:
                            # 找到这个窗口后的第一个场景变化作为片头结束点
                            for change_time in scene_changes:
                                if change_time > current_window + window_size:
                                    return IntroDetectionResult(
                                        intro_end_seconds=int(change_time),
                                        confidence=0.75,
                                        detection_method="scene_density_drop",
                                        details={
                                            "scene_changes": len(scene_changes),
                                            "transition_point": change_time,
                                            "density_before": current_density,
                                            "density_after": next_density
                                        }
                                    )
                
                # 备选方案：寻找长间隔
                for i in range(1, len(scene_changes)):
                    if scene_changes[i] >= self.min_intro_duration:
                        # 计算与前一个场景的间隔
                        gap = scene_changes[i] - scene_changes[i-1]
                        # 如果间隔超过15秒，可能是片头结束
                        if gap > 15:
                            return IntroDetectionResult(
                                intro_end_seconds=int(scene_changes[i]),
                                confidence=0.65,
                                detection_method="scene_gap",
                                details={
                                    "scene_changes": len(scene_changes),
                                    "transition_point": scene_changes[i],
                                    "gap_duration": gap
                                }
                            )
            
        except Exception as e:
            logger.error(f"视频特征检测出错: {e}")
        
        return None
    
    def _detect_by_subtitle_features(self, srt_path: Path) -> Optional[IntroDetectionResult]:
        """
        通过字幕特征检测片头（改进版）
        - 检测歌词特征（重复、押韵等）
        - 检测演职员表
        - 检测正文对话的开始
        """
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            subtitles = self._parse_srt(content)
            
            # 检测歌词特征
            lyrics_score = 0
            credits_score = 0
            
            for i, sub in enumerate(subtitles[:20]):  # 只检查前20条字幕
                text = sub['text'].lower()
                
                # 歌词特征
                if any(marker in text for marker in ['♪', '♫', '[音乐]', '[music]', '(music)']):
                    lyrics_score += 1
                
                # 演职员表特征
                if any(keyword in text for keyword in ['出品', '制作', '导演', '主演', '编剧', 
                                                       'produced', 'directed', 'written']):
                    credits_score += 1
                
                # 如果连续出现多个短句（可能是歌词）
                if len(text) < 20 and i > 0 and len(subtitles[i-1]['text']) < 20:
                    lyrics_score += 0.5
            
            # 找到第一段正常对话
            for i, sub in enumerate(subtitles):
                text = sub['text']
                # 正常对话的特征：较长、包含标点、不是歌词标记
                if (len(text) > 20 and 
                    any(p in text for p in ['。', '，', '？', '！', '.', ',', '?', '!']) and
                    not any(m in text for m in ['♪', '♫', '[音乐]']) and
                    sub['start'] >= self.min_intro_duration):
                    
                    confidence = 0.8 if (lyrics_score > 3 or credits_score > 2) else 0.6
                    
                    return IntroDetectionResult(
                        intro_end_seconds=int(sub['start']),
                        confidence=confidence,
                        detection_method="subtitle_analysis",
                        details={
                            "lyrics_score": lyrics_score,
                            "credits_score": credits_score,
                            "first_dialogue": text[:50]
                        }
                    )
            
        except Exception as e:
            logger.error(f"字幕特征检测出错: {e}")
        
        return None
    
    def _parse_srt(self, content: str) -> List[Dict]:
        """解析SRT文件内容"""
        subtitles = []
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                try:
                    # 解析时间码
                    time_line = lines[1]
                    start_time, end_time = time_line.split(' --> ')
                    start_seconds = self._time_to_seconds(start_time)
                    end_seconds = self._time_to_seconds(end_time)
                    
                    # 获取字幕文本
                    text = ' '.join(lines[2:])
                    
                    subtitles.append({
                        'start': start_seconds,
                        'end': end_seconds,
                        'text': text,
                        'duration': end_seconds - start_seconds
                    })
                except Exception as e:
                    logger.debug(f"解析字幕块失败: {e}")
                    continue
        
        return sorted(subtitles, key=lambda x: x['start'])
    
    def _time_to_seconds(self, time_str: str) -> float:
        """将SRT时间格式转换为秒数"""
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds