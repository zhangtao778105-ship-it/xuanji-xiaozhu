# 玄机小筑

AI 道长在线占卜 Web 应用（Flask）。道长：凤年真人。

## 功能模块

- 周易金钱卦、观音灵签、每日运势、八字命盘、大六壬、风水百科、玄学百科
- AI 解释引擎（DeepSeek API，可降级到静态模板）

## 本地运行

```bash
pip install -r requirements.txt
python app.py
```

访问 `http://127.0.0.1:9090`。

## 云端部署

- **Render**：`https://xuanji-xiaozhu.onrender.com`，Start Command `gunicorn app:app`
  - Render 监听 `main` 分支，本地推送需同时更新 `master` 和 `main`
  - 账号注意：Render 绑定账号需为仓库 collaborator，auto-deploy 才能触发
- 环境变量：`DEEPSEEK_API_KEY`、`CACHE_DIR=/tmp/cache`

## 特殊日期

- 8月6日、8月8日：运势固定「上」（泰卦吉象）
- 7月12日：生日彩蛋，运势「上吉」（乾卦）
