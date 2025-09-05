"""
智能片头检测器 - 使用开源工具和算法
"""
import logging
import subprocess
import json
import cv2
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
from dataclasses import dataclass
import hashlib
from collections import Counter

logger = logging.getLogger(__name__)

@dataclass
class SmartDetectionResult:
    """智能检测结果"""
    intro_end_seconds: float
    outro_start_seconds: Optional[float]  # 片尾开始时间
    confidence: float
    method: str
    details: Dict[str, Any]

class SmartIntroDetector:
    """
    智能片头片尾检测器
    使用多种技术：
    1. PySceneDetect - 场景切换检测
    2. 视频指纹 - 检测重复片段（常见于连续剧）
    3. OCR文字检测 - 识别片头字幕
    4. 音频指纹 - 检测主题曲
    """
    
    def __init__(self):
        self.min_intro = 10  # 最小片头10秒
        self.max_intro = 180  # 最大片头3分钟
        
    def detect(self, video_path: Path) -> SmartDetectionResult:
        """综合检测片头片尾"""
        
        results = []
        
        # 1. 使用PySceneDetect进行场景检测
        try:
            scene_result = self._detect_by_scene_change(video_path)
            if scene_result:
                results.append(scene_result)
        except Exception as e:
            logger.warning(f"场景检测失败: {e}")
        
        # 2. 使用OpenCV进行视觉特征检测
        try:
            visual_result = self._detect_by_visual_features(video_path)
            if visual_result:
                results.append(visual_result)
        except Exception as e:
            logger.warning(f"视觉特征检测失败: {e}")
        
        # 3. 使用ffmpeg进行音频分析
        try:
            audio_result = self._detect_by_audio_features(video_path)
            if audio_result:
                results.append(audio_result)
        except Exception as e:
            logger.warning(f"音频检测失败: {e}")
        
        # 4. 综合所有结果
        if results:
            # 使用投票机制或加权平均
            return self._combine_results(results)
        
        # 默认值
        return SmartDetectionResult(
            intro_end_seconds=60,
            outro_start_seconds=None,
            confidence=0.3,
            method="default",
            details={"reason": "无法检测，使用默认值"}
        )
    
    def _detect_by_scene_change(self, video_path: Path) -> Optional[SmartDetectionResult]:
        """
        使用PySceneDetect检测场景变化
        片头通常有快速的场景切换，然后进入稳定的正文
        """
        try:
            # 使用scenedetect命令行工具
            cmd = [
                "scenedetect",
                "--input", str(video_path),
                "--output", "/tmp",
                "detect-content",
                "--threshold", "30",
                "list-scenes",
                "-f", "json"
            ]
            
            # 如果PySceneDetect未安装，使用ffmpeg替代
            # 检查scenedetect是否可用
            check_cmd = subprocess.run(["which", "scenedetect"], capture_output=True)
            if check_cmd.returncode != 0:
                logger.info("PySceneDetect未安装，使用ffmpeg场景检测")
                return self._detect_by_ffmpeg_scene(video_path)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                # 解析JSON结果
                scenes = json.loads(result.stdout)
                return self._analyze_scene_patterns(scenes)
                
        except Exception as e:
            logger.error(f"PySceneDetect检测失败: {e}")
        
        return None
    
    def _detect_by_ffmpeg_scene(self, video_path: Path) -> Optional[SmartDetectionResult]:
        """使用ffmpeg的场景检测作为后备方案"""
        
        # 检测前3分钟的场景变化
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-t", "180",
            "-vf", "select='gt(scene,0.3)',metadata=print:file=-",
            "-f", "null", "-"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 解析场景变化时间点
            scene_times = []
            for line in result.stderr.split('\n'):
                if "pts_time:" in line:
                    try:
                        time_match = line.split("pts_time:")[1].split()[0]
                        scene_times.append(float(time_match))
                    except:
                        pass
            
            if len(scene_times) > 0:
                # 分析场景变化模式
                return self._analyze_scene_change_pattern(scene_times)
                
        except Exception as e:
            logger.error(f"ffmpeg场景检测失败: {e}")
        
        return None
    
    def _analyze_scene_change_pattern(self, scene_times: List[float]) -> Optional[SmartDetectionResult]:
        """
        分析场景变化模式
        片头特征：前期场景切换频繁，后期趋于稳定
        """
        if len(scene_times) < 3:
            return None
        
        # 计算场景变化密度（每10秒窗口）
        windows = {}
        for time in scene_times:
            window = int(time // 10) * 10
            windows[window] = windows.get(window, 0) + 1
        
        # 找到密度显著下降的点
        sorted_windows = sorted(windows.keys())
        for i in range(len(sorted_windows) - 1):
            current = sorted_windows[i]
            next_w = sorted_windows[i + 1]
            
            # 密度下降超过50%
            if windows[current] >= 3 and windows[next_w] <= 1:
                # 在下一个窗口找到精确的场景变化点
                for time in scene_times:
                    if time > current + 10:
                        if self.min_intro <= time <= self.max_intro:
                            return SmartDetectionResult(
                                intro_end_seconds=time,
                                outro_start_seconds=None,
                                confidence=0.75,
                                method="scene_pattern",
                                details={
                                    "high_density_window": current,
                                    "low_density_window": next_w,
                                    "scene_count": len(scene_times)
                                }
                            )
        
        # 备选：找最长的场景间隔
        if len(scene_times) >= 2:
            gaps = [(scene_times[i+1] - scene_times[i], scene_times[i+1]) 
                    for i in range(len(scene_times)-1)]
            gaps.sort(reverse=True)
            
            # 最长间隔超过15秒，可能是片头结束
            if gaps[0][0] > 15:
                time = gaps[0][1]
                if self.min_intro <= time <= self.max_intro:
                    return SmartDetectionResult(
                        intro_end_seconds=time,
                        outro_start_seconds=None,
                        confidence=0.65,
                        method="scene_gap",
                        details={"gap_duration": gaps[0][0]}
                    )
        
        return None
    
    def _detect_by_visual_features(self, video_path: Path) -> Optional[SmartDetectionResult]:
        """
        使用OpenCV检测视觉特征
        - 检测黑屏、淡入淡出
        - 检测字幕/文字（片头通常有制作信息）
        - 检测logo
        """
        try:
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # 采样分析（每秒1帧）
            frame_interval = int(fps)
            frame_count = 0
            black_frames = []
            text_frames = []
            
            while cap.isOpened() and frame_count < self.max_intro * fps:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_interval == 0:
                    current_time = frame_count / fps
                    
                    # 检测黑屏
                    if self._is_black_frame(frame):
                        black_frames.append(current_time)
                    
                    # 检测文字（简单的边缘检测）
                    if self._has_text(frame):
                        text_frames.append(current_time)
                
                frame_count += 1
            
            cap.release()
            
            # 分析黑屏模式
            if black_frames:
                # 找到最后一个黑屏
                for i in range(len(black_frames) - 1, -1, -1):
                    if self.min_intro <= black_frames[i] <= self.max_intro:
                        # 黑屏后通常是正文开始
                        return SmartDetectionResult(
                            intro_end_seconds=black_frames[i] + 1,
                            outro_start_seconds=None,
                            confidence=0.8,
                            method="black_screen",
                            details={"black_screen_at": black_frames[i]}
                        )
            
            # 分析文字模式（片头通常有密集的文字）
            if text_frames:
                # 找文字密度下降的点
                text_density = self._calculate_density(text_frames)
                drop_point = self._find_density_drop(text_density)
                if drop_point and self.min_intro <= drop_point <= self.max_intro:
                    return SmartDetectionResult(
                        intro_end_seconds=drop_point,
                        outro_start_seconds=None,
                        confidence=0.7,
                        method="text_density",
                        details={"text_frames": len(text_frames)}
                    )
                    
        except Exception as e:
            logger.error(f"OpenCV视觉检测失败: {e}")
        
        return None
    
    def _is_black_frame(self, frame: np.ndarray, threshold: int = 10) -> bool:
        """检测是否为黑屏"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return np.mean(gray) < threshold
    
    def _has_text(self, frame: np.ndarray) -> bool:
        """简单的文字检测（基于边缘）"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        # 边缘像素比例高可能有文字
        edge_ratio = np.sum(edges > 0) / edges.size
        return edge_ratio > 0.02
    
    def _calculate_density(self, times: List[float], window: float = 10) -> Dict[int, int]:
        """计算时间密度"""
        density = {}
        for time in times:
            window_idx = int(time // window)
            density[window_idx] = density.get(window_idx, 0) + 1
        return density
    
    def _find_density_drop(self, density: Dict[int, int], drop_ratio: float = 0.5) -> Optional[float]:
        """找到密度显著下降的点"""
        windows = sorted(density.keys())
        for i in range(len(windows) - 1):
            current = density[windows[i]]
            next_val = density.get(windows[i+1], 0)
            if current >= 3 and next_val / current < drop_ratio:
                return (windows[i] + 1) * 10  # 返回下一个窗口的开始时间
        return None
    
    def _detect_by_audio_features(self, video_path: Path) -> Optional[SmartDetectionResult]:
        """
        音频特征检测
        - 音量分析
        - 静音检测
        - 音频能量分析
        """
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-t", str(self.max_intro),
            "-af", "volumedetect",
            "-f", "null", "-"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 检测静音段
            silence_cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-t", str(self.max_intro),
                "-af", "silencedetect=n=-30dB:d=3",
                "-f", "null", "-"
            ]
            
            silence_result = subprocess.run(silence_cmd, capture_output=True, text=True)
            
            # 解析静音段
            silence_end = None
            for line in silence_result.stderr.split('\n'):
                if "silence_end" in line:
                    try:
                        time = float(line.split("silence_end: ")[1].split()[0])
                        if self.min_intro <= time <= self.max_intro:
                            silence_end = time
                    except:
                        pass
            
            if silence_end:
                return SmartDetectionResult(
                    intro_end_seconds=silence_end,
                    outro_start_seconds=None,
                    confidence=0.8,
                    method="audio_silence",
                    details={"silence_end": silence_end}
                )
                
        except Exception as e:
            logger.error(f"音频检测失败: {e}")
        
        return None
    
    def _combine_results(self, results: List[SmartDetectionResult]) -> SmartDetectionResult:
        """
        综合多个检测结果
        使用加权投票或聚类
        """
        if len(results) == 1:
            return results[0]
        
        # 按置信度排序
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        # 如果最高置信度足够高，直接使用
        if results[0].confidence >= 0.8:
            return results[0]
        
        # 否则，计算加权平均
        total_weight = sum(r.confidence for r in results)
        weighted_time = sum(r.intro_end_seconds * r.confidence for r in results) / total_weight
        
        # 找到最接近加权平均的结果
        closest = min(results, key=lambda r: abs(r.intro_end_seconds - weighted_time))
        
        return SmartDetectionResult(
            intro_end_seconds=round(weighted_time),
            outro_start_seconds=closest.outro_start_seconds,
            confidence=min(0.9, total_weight / len(results)),
            method="weighted_average",
            details={
                "methods": [(r.method, r.intro_end_seconds, r.confidence) for r in results],
                "weighted_time": weighted_time
            }
        )
    
    def detect_by_fingerprint(self, video_path: Path, reference_intros: List[Path] = None) -> Optional[SmartDetectionResult]:
        """
        视频指纹检测（用于系列视频）
        如果有同系列其他视频的片头，可以通过指纹匹配
        """
        # TODO: 实现视频指纹匹配
        # 可以使用 videohash 或 imagehash 库
        pass