import logging
from config import MIN_VIDEO_DURATION

logger = logging.getLogger(__name__)


class SamplingEngine:
    """采样引擎，根据视频时长计算采样点"""
    
    def calculate_sample_points(self, duration_str):
        """
        根据视频时长字符串计算采样点
        
        :param duration_str: 视频时长字符串，如 '3:45' 或 '1:23:45'
        :return: 采样时间点列表（秒）
        """
        duration = self._convert_duration_to_seconds(duration_str)
        
        # 如果视频时长小于最小值，返回空列表
        if duration < MIN_VIDEO_DURATION:
            logger.info(f"视频时长 {duration}s 小于最小值 {MIN_VIDEO_DURATION}s，跳过采样")
            return []
        
        # 计算采样点数量
        if duration < 60:  # 短期视频 (< 60s)
            n = 2
        elif 60 <= duration < 3600:  # 中期视频 (60s - 1小时)
            n = 4
        else:  # 长期视频 (>= 1小时)
            n = max(4, int(duration / 1800))  # 每30分钟增加一个采样点
        
        logger.info(f"视频时长: {duration}s, 采样点数量: {n}")
        
        # 计算采样时间点，避开片头片尾
        # 公式: ti = T / (N+1) * i
        sample_times = []
        for i in range(1, n + 1):
            sample_time = duration / (n + 1) * i
            sample_times.append(sample_time)
        
        logger.info(f"采样时间点: {sample_times}")
        return sample_times

    def _convert_duration_to_seconds(self, duration_str):
        """
        将时长字符串转换为秒数
        :param duration_str: 时长字符串，如 '3:45' 或 '1:23:45'
        :return: 秒数
        """
        try:
            parts = duration_str.split(':')
            if len(parts) == 2:  # MM:SS
                minutes, seconds = parts
                return int(minutes) * 60 + int(seconds)
            elif len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = parts
                return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
            else:
                logger.warning(f"无法解析时长格式: {duration_str}")
                return 0
        except Exception as e:
            logger.error(f"转换时长时出错: {e}")
            return 0