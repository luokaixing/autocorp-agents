# DeFi 项目白皮书库

本目录存放从官方 PDF 白皮书转换的 Markdown 文件，作为 SEO 内容生成的深度素材源。

## 目录结构
- `raw/` — 原始 PDF 文件
- `*.md` — 转换后的 Markdown

## 转换命令
```bash
python -m engine.content_miner --batch company/knowledge/defi-whitepapers/raw/
```

转换单个文件：
```bash
python -m engine.content_miner --file company/knowledge/defi-whitepapers/raw/uniswap-v3.pdf
```

## 转换后端
模块按优先级自动检测可用后端：
1. `mineru` — MinerU (magic-pdf)，保留表格/公式/版面，效果最佳
2. `pdfplumber` — 降级方案，提取文本与段落
3. `pypdf2` — 最基础文本提取
4. `none` — 无可用后端，需安装上述任一库

## 已收录白皮书
- [x] Uniswap V3 白皮书 — https://uniswap.org/whitepaper-v3.pdf （已下载并转换为 `uniswap-v3.md`）
- [x] Compound 白皮书 — https://compound.finance/documents/Compound.Whitepaper.pdf （已下载并转换为 `compound.md`）
- [ ] Aave V3 白皮书 — https://aave.com/docs/ （官方以文档站形式提供，无单一 PDF；可手动导出）
- [ ] Lido 质押协议白皮书 — https://docs.lido.fi/ （官方以文档站形式提供，无传统 PDF 白皮书）
- [ ] Curve 白皮书 — https://github.com/curvefi/stableswap-paper （TeX 源，需手动编译为 PDF）

### 其他可补充的官方白皮书链接
- Uniswap V2: https://uniswap.org/whitepaper.pdf
- Uniswap X: https://uniswap.org/whitepaper-uniswap-x.pdf

## 状态
- 已下载 2 份 PDF 并完成 Markdown 转换（Uniswap V3、Compound）。
- Aave / Lido 官方未提供独立 PDF 白皮书，建议从其文档站导出或人工整理。
- Curve 白皮书为 TeX 源码，需手动编译；待用户补充 PDF 到 `raw/` 后再次执行转换。
