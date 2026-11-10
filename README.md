# 玄机小筑

AI 道长在线占卜 Web 应用（Flask）。道长：凤年真人。

## 功能模块

- 周易金钱卦、观音灵签、每日运势、八字命盘、大六壬、风水百科、玄学百科
- 节气提醒：节气当天首页展示节气卡片（养生建议 / 开运指引 / 五行 / 吉方 / 幸运色）
- AI 解释引擎（DeepSeek API，可降级到静态模板）

## 本地运行

```bash
pip install -r requirements.txt
python app.py
```

访问 `http://127.0.0.1:9090`（启动时打印局域网地址与终端二维码）。

端口默认 9090，可用环境变量覆盖，例如 `PORT=9000 python app.py`。

## 云端部署

- **Render**：`https://xuanji-xiaozhu.onrender.com`
  - Start Command：`gunicorn app:app --bind 0.0.0.0:$PORT`
  - Render 监听 `main` 分支，本地推送需同时更新 `master` 和 `main`
  - 账号注意：Render 绑定账号需为仓库 collaborator，auto-deploy 才能触发
- 环境变量：`DEEPSEEK_API_KEY`、`CACHE_DIR=/tmp/cache`（可选 `AI_API_ENABLED`、`AI_API_MODEL`、`AI_CACHE_TTL_DAYS`、`AI_API_TIMEOUT`、`AI_API_MAX_RETRIES`）
- 其他部署方式：腾讯云 SCF（要求 9000 端口，部署包内 `scf_bootstrap` 已设 `PORT=9000`）、fly.io（`fly.toml`，internal_port 9090）、Dockerfile（EXPOSE 9090）

## 可用性：免费实例休眠与保活

Render 免费 Web Service 在 15 分钟无访问后休眠，下一次访问需 30–60 秒冷启动（期间返回 503 “Application loading”）。当前缓解措施：

- 仓库内 `.github/workflows/keep-alive.yml` 每 5 分钟请求一次 `/healthz` 保活（公共仓库 Actions 免费）
- 免费额度 750 实例小时/月：全天保活约 720–744 小时/月，仍在上限内；请在 Render 面板留意 Instance hours
- ⚠️ GitHub 会停用 60 天无提交仓库的定时工作流，需手动 "Enable workflow"；需要正式宕机告警时另配 UptimeRobot 等监控（探测 `/healthz` 即可）
- `/healthz` 返回轻量 JSON 健康状态，不加载业务数据，适合任何监控/探针

## 并发与 AI 超时

- `gunicorn.conf.py`：1 worker × 8 threads（gthread），AI/网络等待不会阻塞其他访客（Render 启动命令无需改动，gunicorn 会自动加载该文件）
- `ai_interpreter.py`：OpenAI 客户端默认 `timeout=30s`、`max_retries=0`，可用环境变量 `AI_API_TIMEOUT` / `AI_API_MAX_RETRIES` 调整；超时或失败自动降级为静态文案

## 特殊日期

- 8月6日、8月8日：运势固定「上」（泰卦吉象）
- 7月12日：生日彩蛋，运势「上吉」（乾卦）

## 本地开机自启（Windows）

- `launch.vbs`（静默启动）→ `startup.bat` → Flask + natapp 内网穿透（隧道目标 `127.0.0.1:9090`）
- `fix_startup.py` / `fix_startup.bat`：重建开机自启项
