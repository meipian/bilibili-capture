import hashlib
import time
import urllib.parse
import re
import aiohttp
import logging

logger = logging.getLogger(__name__)


async def get_wbi_sign(session):
    """
    获取WBI签名所需的mix密钥
    """
    try:
        resp = await session.get('https://api.bilibili.com/x/web-interface/nav')
        content = await resp.json()
        
        img_url = content['data']['wbi_img']['img_url']
        sub_url = content['data']['wbi_img']['sub_url']
        
        # 提取URL中的参数部分
        img_key = img_url.rsplit('/', 1)[1].split('.')[0]
        sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
        
        return img_key + sub_key
    except Exception as e:
        logger.error(f"获取WBI签名密钥失败: {e}")
        # 这里应该返回一个默认值或者抛出异常，实际应用中需要更健壮的处理
        return "254359c43777d8f2b0e9e3f7d4a5b6c7"


def calculate_wbi_signature(params, mixin_key):
    """
    计算WBI签名
    
    :param params: 请求参数字典
    :param mixin_key: 混合密钥
    :return: 签名字符串
    """
    # 按照键名排序
    ordered_params = dict(sorted(params.items()))
    
    # 构造查询字符串
    query_str = urllib.parse.urlencode(ordered_params)
    
    # 添加mix_key
    sign_str = query_str + mixin_key
    
    # 计算MD5
    signature = hashlib.md5(sign_str.encode()).hexdigest()
    return signature


def convert_duration_to_seconds(duration_str):
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