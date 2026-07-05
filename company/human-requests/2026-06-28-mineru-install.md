# MinerU (magic-pdf) 安装失败与降级记录

记录日期：2026-06-28
任务：integrate-p0-github-tools Task 4 / SubTask 4.1 — 集成 MinerU PDF→Markdown
关联文件：engine/content_miner.py、company/projects/seo-content-generator/requirements.txt

## 事件概述

尝试安装 MinerU (`magic-pdf[full]`) 用于 DeFi 白皮书 PDF 转 Markdown，因网络超时与依赖体积过大失败，已降级为 pdfplumber 后端，功能完整可用。

## 安装尝试明细

| 序号 | 命令 | 镜像 | 结果 |
|------|------|------|------|
| 1 | `pip install "magic-pdf[full]"` | 默认 PyPI | 失败 — `ReadTimeoutError: HTTPSConnectionPool(host='files.pythonhosted.org', port=443): Read timed out`（下载大体积依赖如 torch/opencv 时网络超时） |
| 2 | `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple magic-pdf` | 清华镜像 | 未完成 — 下载耗时超过 5 分钟仍无产出，主动终止（依赖体积大、镜像下载慢） |

## 失败原因分析

1. **依赖体积过大**：`magic-pdf[full]` 拉取 PyTorch、OpenCV、模型推理等重型依赖，单包动辄数百 MB，在当前网络环境下频繁超时。
2. **网络环境受限**：默认 PyPI 源对大文件下载不稳定（ReadTimeout），清华镜像虽可用但整体耗时仍超可接受范围。
3. **Windows 兼容性**：MinerU 部分原生依赖在 Windows 上构建链较复杂，进一步增加安装不确定性。

## 降级处理

按 SubTask 4.1 规定，已实现多后端降级方案：

1. **降级后端**：`pdfplumber 0.11.10`（已成功安装）
   - 安装命令：`pip install --timeout 120 pdfplumber`
   - 依赖：pdfminer.six、pypdfium2、cryptography 等，体积小、安装稳定
2. **`engine/content_miner.py` 自动后端检测**：按优先级 `mineru > pdfplumber > pypdf2 > none`，当前环境自动选中 `pdfplumber`。
3. **功能完整性**：
   - 文本提取：✓ 逐页提取，保留段落
   - 表格提取：✓ 通过 `extract_tables()` 还原表格为 Markdown 表格
   - 批量转换：✓ 已成功转换 Uniswap V3、Compound 两份白皮书
4. **requirements.txt**：已声明 `magic-pdf[full]>=0.10`（首选）与 `pdfplumber>=0.10`（降级），注释说明取舍。

## 与 MinerU 的能力差异

| 能力 | MinerU (magic-pdf) | pdfplumber（当前） |
|------|--------------------|-------------------|
| 纯文本提取 | ✓ | ✓ |
| 表格结构还原 | ✓ 高保真 | ✓ 基础（Markdown 表格） |
| 数学公式识别 | ✓ LaTeX 还原 | ✗ 仅文本 |
| 版面/阅读顺序 | ✓ 智能还原 | ✗ 按页顺序 |
| 图片/图表抽取 | ✓ | ✗ |
| 安装难度 | 高（重依赖） | 低 |

对当前 SEO 内容素材用途（引用白皮书真实数据作为 E-E-A-T 证据），pdfplumber 的文本与表格提取已足够。若后续需要公式/版面高保真，可再尝试安装 MinerU。

## 后续重试建议

1. 在网络稳定时段重试：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple "magic-pdf[full]"`
2. 或使用 conda 环境隔离重型依赖。
3. 安装成功后无需改代码——`content_miner.py` 会自动检测并优先使用 `mineru` 后端。

## 验证结果

- `python -c "from engine.content_miner import ContentMiner; m=ContentMiner(); print(m._backend)"` → 输出 `pdfplumber` ✓
- 单元测试：9 项通过，2 项按预期跳过 ✓
- 实际转换：2/2 PDF 成功（耗时 2.23s）✓
