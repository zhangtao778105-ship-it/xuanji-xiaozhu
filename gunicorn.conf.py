# -*- coding: utf-8 -*-
"""Gunicorn 配置 — 部署（Render / Docker / 本地）时自动加载

为什么这样配：
- 单 worker 多线程（gthread）：Render 免费实例 512MB 内存友好；AI 解释是网络等待，
  多线程可避免「一个顾客算卦时其他访客全部排队」。
- timeout 放宽到 180s：AI 调用客户端已限制 30s 超时，这里留足渲染余量。
- bind 读取 PORT 环境变量：Render 会注入 PORT；本地 gunicorn 默认 10000。
"""

import os

# 监听地址（Render 通过 PORT 环境变量指定端口）
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# 工作进程：免费实例内存有限，1 个 worker + 多线程即可
workers = int(os.environ.get("WEB_CONCURRENCY", "1"))
threads = int(os.environ.get("WEB_THREADS", "8"))
worker_class = "gthread"

# 超时与连接
timeout = 180
graceful_timeout = 30
keepalive = 5

# 日志输出到 stdout/stderr，便于 Render 面板查看
accesslog = "-"
errorlog = "-"
loglevel = "info"
