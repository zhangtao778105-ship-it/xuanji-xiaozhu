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
- 环境变量：`DEEPSEEK_API_KEY`、`CACHE_DIR=/tmp/cache`（可选 `AI_API_ENABLED`、`AI_API_MODEL`、`AI_CACHE_TTL_DAYS`）
- 其他部署方式：腾讯云 SCF（要求 9000 端口，部署包内 `scf_bootstrap` 已设 `PORT=9000`）、fly.io（`fly.toml`，internal_port 9090）、Dockerfile（EXPOSE 9090）

## 特殊日期

- 8月6日、8月8日：运势固定「上」（泰卦吉象）
- 7月12日：生日彩蛋，运势「上吉」（乾卦）

## 本地开机自启（Windows）

- `launch.vbs`（静默启动）→ `startup.bat` → Flask + natapp 内网穿透（隧道目标 `127.0.0.1:9090`）
- `fix_startup.py` / `fix_startup.bat`：重建开机自启项
