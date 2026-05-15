# Strategy Canvas — Render 部署配置

## 一键部署

1. 把代码推到 GitHub（已完成 ✅）
2. 去 [render.com](https://render.com) 注册，点 "New Web Service"
3. 选这个 repo，Render 会自动识别 Python 项目，填：

```
Build Command:   pip install -r requirements.txt
Start Command:   python main.py --port 10000
```

4. 在 Environment Variables 里加：
```
DEEPSEEK_API_KEY=sk-39f669dca4c749c2ad5c8d02db00a3e9
```

5. 点 Deploy，2-3 分钟后拿到 `https://strategy-canvas.onrender.com`

## Free Tier 限制
- 15 分钟无请求自动休眠（下次请求 ~30s 冷启动）
- 每月 750 小时

## 保持活跃（可选）
用 [cron-job.org](https://cron-job.org) 每 10 分钟 ping 一次你的 URL 就不会休眠。
