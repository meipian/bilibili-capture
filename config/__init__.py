"""
配置管理模块
"""
from config.config import *
from config.config_manager import load_user_config, save_user_config

__all__ = ["load_user_config", "save_user_config"]
