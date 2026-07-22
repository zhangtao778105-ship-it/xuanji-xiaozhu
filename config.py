# -*- coding: utf-8 -*-
"""全局配置"""

import os

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
except ImportError:
    pass

# 服务配置
HOST = "0.0.0.0"
PORT = 9000  # SCF Web Function 要求 9000 端口
DEBUG = False

# 项目路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# 时区配置（PythonAnywhere 是 UTC，需显式设为东八区）
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Shanghai")

# 道长配置
PRIEST_NAME = "凤年真人"
PRIEST_TITLE = "玄机小筑 · 掌院真人"
SITE_TITLE = "玄机小筑"

# AI 配置（从环境变量读取）
AI_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
AI_API_ENABLED = os.environ.get("AI_API_ENABLED", "true").lower() == "true"
AI_API_MODEL = os.environ.get("AI_API_MODEL", "deepseek-chat")
AI_CACHE_TTL_DAYS = int(os.environ.get("AI_CACHE_TTL_DAYS", "90"))
