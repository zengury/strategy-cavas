# Strategy Canvas — Render 部署

## 一键部署

1. 去 [render.com](https://render.com) 注册（GitHub 登录即可）
2. 点 **New + → Web Service**
3. 连接 `zengury/strategy-cavas` 仓库
4. Render 自动识别 `render.yaml`，只需手动填一个环境变量：

   ```
   DEEPSEEK_API_KEY = sk-39f669dca4c749c2ad5c8d02db00a3e9
   ```

5. 点 **Create Web Service**，等 2-3 分钟部署完成
6. 拿到 `https://strategy-canvas-xxxx.onrender.com`

## Free Tier
- 15 分钟无请求自动休眠，下次访问冷启动 ~30s
- 每月 750 小时运行时间

## 防休眠（可选）
用 [cron-job.org](https://cron-job.org) 每 10 分钟 ping 一次你的 URL
