# 人工协助记录：Chrome 内核下载受阻

- 日期：2026-06-27
- 任务：用 agent-browser 自动化 Publish0x 跨平台发布
- 阻塞点：googlechromelabs.github.io / storage.googleapis.com 下载 Chrome 内核失败
  - 首次：连接被强制关闭（10054）
  - 翻墙后重试：下载到 20% 超时
  - 第三次：版本信息接口再次 10054
- 用户已开翻墙但不稳定
- 降级方案：用户手动操作 Publish0x（复制粘贴 3-5 分钟）
- 后续：若需要真实自动化，需稳定翻墙或使用国内 Chromium 镜像

# 影响范围
- Publish0x 跨平台发布 → 改手动
- Twitter 发推文 → 改手动（用户未登录 Twitter）
- Reddit 养号 → 改手动（用户未登录 Reddit）
