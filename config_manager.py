import json
import os
from config import *

CONFIG_FILE = 'user_config.json'

def save_user_config(config_data):
    """保存用户配置到文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        print(f"配置已保存到 {CONFIG_FILE}")
    except Exception as e:
        print(f"保存配置时出错: {e}")

def load_user_config():
    """从文件加载用户配置"""
    if not os.path.exists(CONFIG_FILE):
        # 如果配置文件不存在，返回默认值
        return {
            'cookie': BILIBILI_COOKIE,
            'target_up_id': TARGET_UP_ID,
            'favorite_list_id': FAVORITE_LIST_ID,
            'start_year': START_YEAR,
            'start_month': START_MONTH,
            'start_day': START_DAY,
            'end_year': END_YEAR,
            'end_month': END_MONTH,
            'end_day': END_DAY,
            'max_qps': MAX_QPS,
            'concurrent_limit': CONCURRENT_LIMIT,
            'output_dir': OUTPUT_DIR,
            'image_format': IMAGE_FORMAT,
            'debug_mode': DEBUG_MODE
        }
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置时出错: {e}")
        # 出错时返回默认值
        return {
            'cookie': BILIBILI_COOKIE,
            'target_up_id': TARGET_UP_ID,
            'favorite_list_id': FAVORITE_LIST_ID,
            'start_year': START_YEAR,
            'start_month': START_MONTH,
            'start_day': START_DAY,
            'end_year': END_YEAR,
            'end_month': END_MONTH,
            'end_day': END_DAY,
            'max_qps': MAX_QPS,
            'concurrent_limit': CONCURRENT_LIMIT,
            'output_dir': OUTPUT_DIR,
            'image_format': IMAGE_FORMAT,
            'debug_mode': DEBUG_MODE
        }