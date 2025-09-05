"""
片头检测工具 - 自动检测并标记视频片头部分
"""
import logging
from typing import Optional, Tuple, List, Dict
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class IntroDetector:
    """片头检测器"""
    
    def __init__(self, 
                 min_dialogue_density: float = 0.3,  # 最小对话密度（每10秒至少3句话）
                 silence_threshold: int = 30,         # 静音阈值（连续30秒无对话判定为片头）
                 min_intro_duration: int = 20,        # 最小片头时长（秒）
                 max_intro_duration: int = 120,       # 最大片头时长（秒）
                 default_intro_duration: int = 60):   # 默认片头时长（秒）
        
        self.min_dialogue_density = min_dialogue_density
        self.silence_threshold = silence_threshold
        self.min_intro_duration = min_intro_duration
        self.max_intro_duration = max_intro_duration
        self.default_intro_duration = default_intro_duration
    
    def detect_intro_from_srt(self, srt_path: Path) -> Tuple[int, str]:
        """
        通过分析SRT字幕文件检测片头结束时间
        
        Args:
            srt_path: SRT字幕文件路径
            
        Returns:
            (片头结束时间秒数, 检测理由)
        """
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析SRT文件
            subtitles = self._parse_srt(content)
            
            if not subtitles:
                logger.warning("字幕文件为空，使用默认片头时长")
                return self.default_intro_duration, "字幕文件为空，使用默认值"
            
            # 策略1：检测第一段密集对话的开始
            intro_end_1, reason_1 = self._detect_by_dialogue_density(subtitles)
            
            # 策略2：检测长时间静音后的第一句话
            intro_end_2, reason_2 = self._detect_by_silence_break(subtitles)
            
            # 选择更合理的结果
            if intro_end_1 > 0 and self.min_intro_duration <= intro_end_1 <= self.max_intro_duration:
                return intro_end_1, reason_1
            elif intro_end_2 > 0 and self.min_intro_duration <= intro_end_2 <= self.max_intro_duration:
                return intro_end_2, reason_2
            else:
                # 如果都不合理，使用默认值
                return self.default_intro_duration, "检测结果不在合理范围内，使用默认值"
                
        except Exception as e:
            logger.error(f"检测片头失败: {e}")
            return self.default_intro_duration, f"检测失败: {str(e)}"
    
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
        # 格式: 00:01:23,456
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    
    def _detect_by_dialogue_density(self, subtitles: List[Dict]) -> Tuple[int, str]:
        """通过对话密度检测片头结束位置"""
        if not subtitles:
            return -1, ""
        
        # 计算每10秒窗口的对话数量
        window_size = 10  # 10秒窗口
        current_window_start = 0
        dialogue_count = 0
        
        for subtitle in subtitles:
            # 如果超出当前窗口，检查密度
            while subtitle['start'] >= current_window_start + window_size:
                density = dialogue_count / window_size
                
                # 如果密度足够高，认为正式内容开始
                if density >= self.min_dialogue_density:
                    # 返回这个窗口的开始时间作为片头结束时间
                    return int(current_window_start), f"检测到密集对话开始于{int(current_window_start)}秒"
                
                # 移动到下一个窗口
                current_window_start += window_size
                dialogue_count = 0
            
            # 统计当前窗口的对话
            if subtitle['start'] >= current_window_start:
                # 过滤掉过短的字幕（可能是音效说明）
                if len(subtitle['text'].strip()) > 5:
                    dialogue_count += 1
        
        return -1, "未检测到密集对话"
    
    def _detect_by_silence_break(self, subtitles: List[Dict]) -> Tuple[int, str]:
        """检测长时间静音后的第一句话"""
        if not subtitles:
            return -1, ""
        
        # 检查第一句话之前的静音
        first_dialogue_time = subtitles[0]['start']
        if first_dialogue_time >= self.min_intro_duration:
            return int(first_dialogue_time), f"第一句对话出现在{int(first_dialogue_time)}秒"
        
        # 检查字幕之间的间隔
        for i in range(len(subtitles) - 1):
            current_end = subtitles[i]['end']
            next_start = subtitles[i + 1]['start']
            gap = next_start - current_end
            
            # 如果间隔超过阈值，认为是片头和正文的分界
            if gap >= self.silence_threshold:
                return int(next_start), f"检测到{int(gap)}秒的静音间隔后开始正文"
        
        return -1, "未检测到明显的静音间隔"
    
    def adjust_srt_timeline(self, srt_path: Path, offset_seconds: float, output_path: Optional[Path] = None) -> Path:
        """
        调整SRT字幕的时间轴
        
        Args:
            srt_path: 原始SRT文件路径
            offset_seconds: 时间偏移量（负数表示提前）
            output_path: 输出路径，如果为None则覆盖原文件
            
        Returns:
            调整后的SRT文件路径
        """
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 正则表达式匹配时间码
        time_pattern = r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})'
        
        def adjust_time(time_str: str) -> str:
            """调整单个时间码"""
            seconds = self._time_to_seconds(time_str)
            new_seconds = max(0, seconds - offset_seconds)  # 确保不会变成负数
            
            # 转换回时间格式
            hours = int(new_seconds // 3600)
            minutes = int((new_seconds % 3600) // 60)
            secs = new_seconds % 60
            millisecs = int((secs % 1) * 1000)
            secs = int(secs)
            
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
        
        # 替换所有时间码
        def replace_times(match):
            start_time = adjust_time(match.group(1))
            end_time = adjust_time(match.group(2))
            
            # 如果整个字幕都在片头范围内，则跳过这个字幕
            if self._time_to_seconds(match.group(2)) <= offset_seconds:
                return None
            
            return f"{start_time} --> {end_time}"
        
        # 处理字幕块
        blocks = content.strip().split('\n\n')
        adjusted_blocks = []
        block_number = 1
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                # 检查时间码
                time_match = re.search(time_pattern, lines[1])
                if time_match:
                    # 如果结束时间在片头之前，跳过这个字幕
                    end_seconds = self._time_to_seconds(time_match.group(2))
                    if end_seconds <= offset_seconds:
                        continue
                    
                    # 调整时间码
                    new_time_line = re.sub(time_pattern, replace_times, lines[1])
                    if new_time_line:
                        # 重新编号并添加调整后的字幕块
                        adjusted_block = f"{block_number}\n{new_time_line}\n" + '\n'.join(lines[2:])
                        adjusted_blocks.append(adjusted_block)
                        block_number += 1
        
        adjusted_content = '\n\n'.join(adjusted_blocks)
        
        # 保存调整后的字幕
        if output_path is None:
            output_path = srt_path
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(adjusted_content)
        
        logger.info(f"字幕时间轴已调整 {offset_seconds} 秒")
        return output_path