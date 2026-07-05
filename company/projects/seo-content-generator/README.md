# SEO Content Generator

AutoCorp 首个商业化产品 MVP：基于 LLM 抽象层的 SEO 内容自动化生成器 CLI 工具。

输入种子关键词 + 目标语言，自动生成一篇 SEO 优化的长文（≥1500 字），含标题、Meta description、H1/H2/H3 结构、内链建议与 SEO 评分。

## 特性

- **零外部依赖可用**：内置 `TemplateProvider` 基于规则与模板生成真实可用的 SEO 内容，无需任何 LLM API Key。
- **多后端 LLM 抽象**：`LLMProvider` 抽象层支持 `template`（兜底）与 `openai`（OpenAI 兼容接口）两种后端，可平滑切换。
- **完整 SEO 输出**：关键词分析 → 大纲 → 正文 → 评分，全流程自动化。
- **质量保证**：关键词密度自动校准至 1-2%，H1/H2/H3 层级完整，SEO 评分 ≥70。
- **中英双语**：支持中文与英文内容生成。

## 安装

```bash
cd company/projects/seo-content-generator
pip install -r requirements.txt
```

依赖：`click>=8.0`、`pyyaml>=6.0`（与 AutoCorp 主项目一致）。

## 快速开始

### 生成完整 SEO 文章

```bash
py -m seo_generator generate --keyword "email marketing" --lang en --output article.md
```

生成的 `article.md` 含 YAML frontmatter（title / description / keywords / seo_score）与完整 Markdown 正文。

### 仅分析关键词

```bash
py -m seo_generator analyze --keyword "email marketing"
```

### 命令参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--keyword / -k` | 种子关键词（必填） | - |
| `--lang / -l` | 目标语言：`en` / `zh` | `en` |
| `--audience / -a` | 目标受众描述 | `general` |
| `--output / -o` | 输出文件路径；不指定则打印到 stdout | - |
| `--provider / -p` | LLM 提供方：`template` / `openai` | `template` |

## 架构

```
seo_generator/
├── __init__.py            # 包定义与版本号
├── __main__.py            # 支持 py -m seo_generator 调用
├── cli.py                 # Click CLI 入口（generate / analyze 命令）
├── llm_provider.py        # LLM 抽象层 + TemplateProvider 兜底实现
├── templates.py           # 提示词模板与兜底内容模板
├── keyword_analyzer.py    # 关键词分析与长尾词扩展
├── outline_generator.py   # 文章大纲生成（H1/H2/H3）
├── content_writer.py      # 正文写作 + meta + 内链
└── seo_scorer.py          # 多维度 SEO 评分
```

### 生成流程

```
种子关键词
    │
    ▼
KeywordAnalyzer.analyze()  ──→ {primary_keyword, secondary_keywords, long_tail, search_intent}
    │
    ▼
OutlineGenerator.generate() ──→ {h1, sections: [{h2, h3_list}]}
    │
    ▼
ContentWriter.write()      ──→ {meta_description, body_markdown, internal_links, word_count}
    │
    ▼
SEOScorer.score()          ──→ {score(0-100), suggestions[]}
    │
    ▼
Markdown 文件（含 frontmatter）
```

### LLM 抽象层

`LLMProvider` 抽象基类定义统一接口 `generate(system_prompt, user_message) -> str`：

- **`TemplateProvider`**（默认）：基于 `templates.py` 的规则与模板生成结构化内容，不依赖任何外部 API。通过 system_prompt 中的任务标记（`[TASK:KEYWORD_ANALYSIS]` / `[TASK:OUTLINE_GENERATION]` / `[TASK:CONTENT_WRITING]`）路由到对应生成逻辑。
- **`OpenAICompatibleProvider`**（可选）：调用 OpenAI 兼容 `chat/completions` 接口，需提供 `base_url` / `api_key` / `model`。延迟导入 `openai`，未安装时不影响 TemplateProvider。

工厂函数 `get_provider(name="template")` 返回对应实例。

### 关键词密度优化

`TemplateProvider` 生成正文后，自动调用 `optimize_keyword_density()` 校准关键词密度：
- 保留标题与内链中的关键词（SEO 最佳实践）。
- 把正文中超出的关键词替换为代词变体（this strategy / this approach ...）。
- 两阶段替换：先替换独立关键词，再替换 "关键词+名词" 复合词。
- 目标密度 1.4%，确保落在 1-2% 区间。

### SEO 评分维度

| 维度 | 权重 | 满分标准 |
|------|------|----------|
| 关键词密度 | 20% | 1-2% |
| 标题结构 | 20% | 含 H1+H2+H3 |
| 字数 | 15% | ≥1500 字 |
| H2/H3 层级 | 15% | ≥3 个 H2 且每个 H2 下有 H3 |
| 内链 | 15% | ≥3 个 |
| Meta description | 15% | 长度 120-155 字符且含主关键词 |

## 扩展方式

### 接入真实 LLM

1. 安装 OpenAI SDK：`pip install openai`
2. 使用 `openai` provider：

```python
from seo_generator.llm_provider import get_provider
from seo_generator.keyword_analyzer import KeywordAnalyzer

provider = get_provider("openai", base_url="https://api.openai.com/v1",
                        api_key="sk-...", model="gpt-4o-mini")
analyzer = KeywordAnalyzer(provider=provider)
analysis = analyzer.analyze("email marketing", language="en")
```

3. 或通过 CLI：`py -m seo_generator generate -k "email marketing" -p openai`

> 注：`OpenAICompatibleProvider` 生成的内容可能不严格符合 JSON 格式，各模块均有本地规则兜底解析失败的情况。

### 自定义模板

编辑 `seo_generator/templates.py`：
- `SECTION_PARAGRAPHS_EN` / `SECTION_PARAGRAPHS_ZH`：段落内容模板。
- `OUTLINE_TEMPLATE_EN` / `OUTLINE_TEMPLATE_ZH`：大纲章节模板。
- `INTERNAL_LINK_TEMPLATES_*`：内链锚文本模板。

## 测试

```bash
py -m unittest discover tests -v
```

测试覆盖：
- 关键词分析结构
- 大纲生成结构
- 完整生成流程（字数、H1/H2/H3、关键词密度、SEO 评分）
- 中英文双语生成
- CLI generate / analyze 命令
- SEO 评分器边界用例

## 项目约束

- TemplateProvider 必须能独立工作，不依赖任何外部 API。
- 内容质量真实可用（非占位文本）。
- 代码风格与 AutoCorp 主项目一致：中文注释、类型提示、docstring。
- 不修改 AutoCorp 主项目（`engine/` 等核心引擎）。

## 许可

AutoCorp 内部产品，版权所有。
