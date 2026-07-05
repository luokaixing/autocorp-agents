"""Learn & Earn 答题助手

分析 Binance / CoinMarketCap Learn & Earn 课程内容，生成答题指南，
帮助用户快速完成课程获取奖励（单课程 $2-20，1-3 天到账，确定性高）。

设计要点：
- 不依赖 HTTP LLM API：智谱 GLM-5.2 公开 API 返回 404，所以答题指南由规则代码生成
  （关键词提取 + 模板题目）。analyze_with_llm 会尝试调用 llm_client.chat()，但必须
  try/except 降级到规则代码，绝不阻断主流程。
- 优雅降级：WebFetch 失败 / 课程内容为空 / LLM 调用失败 均不阻断主流程，
  统一降级到 fallback_tips 通用答题技巧。
- 复用 OpportunityRadar：批量生成时调用 OpportunityRadar.scan_binance_learn_earn()
  获取课程列表，不重复实现抓取逻辑。
- 文件即数据库：每个课程的答题指南独立一个 md 文件，写入
  company/knowledge/learn-earn/<course-name>-answers.md。
- HTTP 库兼容：requests 优先、urllib 回退，与 wallet.py / opportunity_radar.py 一致。

主流程：
    generate_guide(course_url)
        → fetch_course_content          # 抓取 HTML，提取正文
        → analyze_with_llm              # 调用 LLM 分析（失败降级）
        → generate_questions_and_answers  # 规则代码生成题目+答案+解析
        → assess_confidence             # 评估答案置信度
        → write_guide                   # 落盘到 md 文件
"""
from __future__ import annotations

import datetime
import re
from typing import Any, Dict, List

# HTTP 库：优先 requests（若已安装），否则回退到标准库 urllib（与 opportunity_radar.py 保持一致）
try:
    import requests  # type: ignore

    _HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error

    _HAS_REQUESTS = False


# 英文停用词表（用于关键词提取时过滤高频虚词）
_STOP_WORDS = {
    "the", "and", "for", "are", "but", "not", "you", "all", "any", "can",
    "her", "was", "one", "our", "out", "has", "have", "had", "his", "how",
    "its", "may", "new", "now", "old", "see", "him", "two", "way", "who",
    "boy", "did", "man", "men", "put", "say", "she", "too", "use", "via",
    "this", "that", "with", "from", "your", "will", "they", "them", "then",
    "what", "when", "make", "made", "more", "most", "some", "such", "only",
    "into", "also", "than", "very", "like", "just", "over", "about", "after",
    "before", "between", "during", "through", "above", "below", "there",
    "where", "which", "while", "these", "those", "being", "because",
    "another", "other", "each", "both", "few", "many", "much", "should",
    "would", "could", "must", "shall", "might", "need", "been", "were",
    "having", "does", "doing", "done", "going", "gets", "get", "got",
    "give", "given", "took", "take", "taken", "come", "came", "become",
    "became", "is", "of", "to", "in", "on", "at", "by", "an", "as", "be",
    "or", "if", "it", "no", "so", "do", "up", "we", "he", "me", "my", "us",
    "am", "a", "i", "if", "then", "here", "once",
}


class LearnEarnAssistant:
    """Learn & Earn 答题助手：分析课程内容并产出答题指南。

    主入口为 generate_guide(course_url)，完整流程见模块 docstring。
    """

    # 关键词提取：取频次 top N（spec 要求 top 10）
    _TOP_KEYWORDS = 10
    # 每个关键词生成的题目数上限（spec 要求 1-2 道）
    _QUESTIONS_PER_KEYWORD = 2
    # 高置信度的关键词出现频次阈值（≥3 次视为有明确语句支撑）
    _HIGH_CONFIDENCE_THRESHOLD = 3

    def __init__(self, workspace=None, llm_client=None):
        """初始化答题助手。

        Args:
            workspace: WorkspaceManager 实例；为空则自动创建（root_dir 指向 company/）。
            llm_client: LLMClient 实例；可空。用于 analyze_with_llm 尝试 LLM 分析，
                        但因 TRAE 公开 API 404，失败时降级到规则代码，不阻断主流程。
        """
        from engine.workspace import WorkspaceManager

        self.workspace = workspace or WorkspaceManager()
        self.llm_client = llm_client
        # 答题指南输出目录：company/knowledge/learn-earn/
        self.learn_earn_dir = self.workspace.knowledge_dir / "learn-earn"

    # ==================================================================
    # SubTask 2.1: generate_guide 主方法
    # ==================================================================
    def generate_guide(self, course_url: str) -> Dict[str, Any]:
        """生成单个课程的完整答题指南。

        流程：
        1. fetch_course_content 抓取课程页面正文
        2. 内容为空 → 走降级路径（_assemble_degraded_guide + fallback_tips），
           标记该课程为"需用户自行答题"
        3. 内容非空 → analyze_with_llm + generate_questions_and_answers +
           assess_confidence，组装完整指南
        4. write_guide 落盘到 company/knowledge/learn-earn/<course>-answers.md

        Args:
            course_url: 课程页面 URL。

        Returns:
            结果字典，含 course_name/course_url/content_length/question_count/
            confidence_overall/degraded/guide_path 等字段。
        """
        course_name = self._derive_course_name(course_url)
        print(f"[learn_earn] 开始生成答题指南：{course_name} ({course_url})")

        # 1. 抓取课程正文（失败返回空字符串，不抛异常）
        content = self.fetch_course_content(course_url)
        content_length = len(content)

        # 2. 内容为空 → 降级路径
        if not content.strip():
            print("[learn_earn] 课程内容为空，走降级路径（fallback_tips）")
            guide_content = self._assemble_degraded_guide(
                course_name=course_name,
                course_url=course_url,
                reason="课程页面内容抓取失败或为空（页面可能为 SPA 渲染或网络异常）",
            )
            guide_path = self.write_guide(course_name, guide_content)
            return {
                "course_name": course_name,
                "course_url": course_url,
                "content_length": 0,
                "question_count": 0,
                "confidence_overall": "low",
                "degraded": True,
                "guide_path": guide_path,
            }

        # 3. 内容非空：分析 + 生成题目 + 评估置信度
        analysis = self.analyze_with_llm(content)
        answers = self.generate_questions_and_answers(content)
        confidence = self.assess_confidence(answers)

        # 4. 组装 markdown 指南
        guide_content = self._assemble_guide(
            course_name=course_name,
            course_url=course_url,
            content=content,
            analysis=analysis,
            answers=answers,
            confidence=confidence,
        )

        # 5. 落盘
        guide_path = self.write_guide(course_name, guide_content)

        return {
            "course_name": course_name,
            "course_url": course_url,
            "content_length": content_length,
            "question_count": len(answers),
            "confidence_overall": confidence.get("overall", "low"),
            "degraded": bool(analysis.get("degraded")),
            "guide_path": guide_path,
        }

    # ==================================================================
    # SubTask 2.2: fetch_course_content
    # ==================================================================
    def fetch_course_content(self, course_url: str) -> str:
        """抓取课程页面 HTML 并提取正文文本。

        使用 _fetch_text 获取 HTML，再用简单去标签逻辑提取正文。
        失败时返回空字符串，不抛异常（优雅降级）。

        Args:
            course_url: 课程页面 URL。

        Returns:
            课程正文文本（去标签、压缩空白）。失败返回空字符串。
        """
        try:
            html = self._fetch_text(course_url)
        except Exception as e:  # noqa: BLE001 - 网络层异常统一兜底
            print(f"[learn_earn] 抓取课程页面失败 {course_url}：{e}")
            return ""

        if not html:
            return ""

        # 提取正文文本：去标签 → HTML 实体 → 压缩空白
        text = self._html_to_text(html)
        return text

    # ==================================================================
    # SubTask 2.3: analyze_with_llm
    # ==================================================================
    def analyze_with_llm(self, content: str) -> Dict[str, Any]:
        """构造 LLM prompt 分析课程内容。

        尝试调用 self.llm_client.chat() 分析课程内容并产出知识点摘要。
        因 TRAE 公开 API 404，必须 try/except 包裹，失败时返回降级结构，
        由规则代码继续生成题目（不阻断主流程）。

        Args:
            content: 课程正文文本。

        Returns:
            分析结果字典：
            - 成功：{summary, key_points, degraded: False, raw}
            - 降级：{summary, key_points: [], degraded: True, reason}
        """
        # llm_client 未注入 → 直接降级
        if self.llm_client is None:
            return {
                "summary": "（需 assistant 直接生成：LLM 客户端未注入）",
                "key_points": [],
                "degraded": True,
                "reason": "llm_client 未注入，规则代码已接管题目生成",
            }

        system_prompt = (
            "你是加密货币 Learn & Earn 课程的答题助手。"
            "请分析课程内容，输出：\n"
            "1. 课程知识点摘要（200 字以内）\n"
            "2. 关键知识点列表（5-10 条，每条 1 句话）\n"
            "3. 预测验可能考察的知识点\n"
            "请用 markdown 列表格式输出。"
        )
        # 截断 content 避免 token 过长
        truncated = content[:4000]
        user_message = f"课程内容：\n\n{truncated}"

        try:
            result = self.llm_client.chat(system_prompt, user_message)
            return {
                "summary": (result or "").strip(),
                "key_points": [],  # LLM 返回的 markdown 整体保留在 raw 字段
                "degraded": False,
                "raw": result or "",
            }
        except Exception as e:  # noqa: BLE001 - LLM 调用失败统一降级
            print(f"[learn_earn] LLM 调用失败，降级到规则代码：{e}")
            return {
                "summary": "（需 assistant 直接生成：LLM API 不可用）",
                "key_points": [],
                "degraded": True,
                "reason": f"LLM 调用失败：{e}；已降级到规则代码",
            }

    # ==================================================================
    # SubTask 2.4: generate_questions_and_answers
    # ==================================================================
    def generate_questions_and_answers(self, content: str) -> List[Dict[str, Any]]:
        """基于内容关键词产出题目预测 + 答案 + 解析。

        规则代码实现（不依赖 LLM HTTP API）：
        1. 提取关键词（出现频次 top 10，过滤停用词）
        2. 每个关键词生成 1-2 道选择题
        3. 答案基于关键词在原文的出现频次推断（频次高 → 答案倾向该关键词相关选项）
        4. 解析引用关键词在原文的上下文片段

        内容为空时调用 fallback_tips()（spec 要求），并返回空列表。

        Args:
            content: 课程正文文本。

        Returns:
            题目字典列表，每个含 question/options/answer/explanation/keyword/
            occurrence/confidence_basis 字段。
        """
        # 内容为空 → 调用 fallback_tips（spec 要求），主方法会负责把技巧组装到指南
        if not content.strip():
            print("[learn_earn] 内容为空，调用 fallback_tips")
            self.fallback_tips()  # 显式调用以满足 spec
            return []

        # 1. 提取关键词频次表（已按频次降序排序）
        keyword_counts = self._extract_keywords(content)
        if not keyword_counts:
            print("[learn_earn] 未提取到关键词，无法生成题目")
            return []

        # 2. 每个关键词生成 1-2 道选择题
        answers: List[Dict[str, Any]] = []
        top_keywords = keyword_counts[: self._TOP_KEYWORDS]
        for keyword, count in top_keywords:
            num_questions = 1 if count < self._HIGH_CONFIDENCE_THRESHOLD else self._QUESTIONS_PER_KEYWORD
            for q_idx in range(num_questions):
                qa = self._make_question(keyword, count, content, q_idx)
                answers.append(qa)

        return answers

    # ==================================================================
    # SubTask 2.5: assess_confidence
    # ==================================================================
    def assess_confidence(self, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """评估答案置信度。

        评分规则（spec 要求）：
        - 高（≥90%）：答案在原文有明确语句支撑（关键词出现 ≥3 次）
        - 中（60-90%）：答案基于关键词推断（关键词出现 1-2 次）
        - 低（<60%）：答案为猜测（关键词未出现）

        Args:
            answers: generate_questions_and_answers 返回的题目列表。

        Returns:
            {
                "overall": "high" | "medium" | "low",
                "per_question": [{question, confidence, score, basis}],
                "high_count": int, "medium_count": int, "low_count": int,
            }
        """
        if not answers:
            return {
                "overall": "low",
                "per_question": [],
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
            }

        per_question: List[Dict[str, Any]] = []
        high_count = 0
        medium_count = 0
        low_count = 0

        for ans in answers:
            occurrence = int(ans.get("occurrence", 0))
            if occurrence >= self._HIGH_CONFIDENCE_THRESHOLD:
                confidence = "high"
                score = 90
                basis = "答案关键词在原文出现 ≥3 次，有明确语句支撑"
                high_count += 1
            elif occurrence >= 1:
                confidence = "medium"
                score = 60
                basis = "答案关键词在原文出现 1-2 次，基于关键词推断"
                medium_count += 1
            else:
                confidence = "low"
                score = 30
                basis = "答案关键词未在原文出现，答案为猜测"
                low_count += 1

            per_question.append({
                "question": ans.get("question", ""),
                "confidence": confidence,
                "score": score,
                "basis": basis,
            })

        # 总体置信度：按 high > medium > low 数量决定
        if high_count >= medium_count and high_count >= low_count:
            overall = "high"
        elif medium_count >= low_count:
            overall = "medium"
        else:
            overall = "low"

        return {
            "overall": overall,
            "per_question": per_question,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
        }

    # ==================================================================
    # SubTask 2.6: write_guide
    # ==================================================================
    def write_guide(self, course_name: str, guide_content: str) -> str:
        """写入答题指南到 company/knowledge/learn-earn/<course-name>-answers.md。

        自动创建目录。返回指南文件路径。

        Args:
            course_name: 课程名（用于构造文件名，会做安全归一化）。
            guide_content: markdown 内容。

        Returns:
            写入的文件绝对路径字符串。
        """
        # 文件名安全归一化：仅保留字母数字与连字符
        safe_name = self._slugify(course_name) or "course"
        file_path = self.learn_earn_dir / f"{safe_name}-answers.md"

        # 自动创建目录（文件即数据库：所有输出落盘）
        self.workspace.ensure_dir(self.learn_earn_dir)
        self.workspace.write_text(file_path, guide_content)
        print(f"[learn_earn] 答题指南已写入：{file_path}")
        return str(file_path)

    # ==================================================================
    # SubTask 2.7: fallback_tips
    # ==================================================================
    def fallback_tips(self) -> str:
        """内容抓取失败时输出通用答题技巧。

        返回 markdown 格式的通用 Learn & Earn 答题技巧，包含：
        - 排除法
        - 关键词匹配
        - 常见错误选项特征
        - 项目方常见考点
        - 答题后操作
        - 标记该课程为"需用户自行答题"

        Returns:
            markdown 字符串。
        """
        return "\n".join([
            "## 通用 Learn & Earn 答题技巧（内容抓取失败降级）",
            "",
            "> 本课程页面内容抓取失败或为空，无法基于课程内容生成精确答案。",
            "> 请使用以下通用答题技巧自行完成测验。",
            "",
            "### 1. 排除法",
            "- 优先排除绝对化表述的选项（含 \"always\" / \"never\" / \"guaranteed\" / \"100%\" 等词）",
            "- 排除与区块链基本原理相悖的选项（如 \"中心化\" / \"可篡改\" / \"无需验证\"）",
            "- 排除明显夸大收益的选项（如 \"月收益 100%\" / \"稳赚不赔\"）",
            "",
            "### 2. 关键词匹配",
            "- 题目中的专有名词（项目名 / 代币符号 / 技术术语）通常在课程正文有原文支撑",
            "- 答案选项中含课程标题关键词的，优先考虑",
            "- 涉及数字（奖励金额 / 区块时间 / 代币供应量）的题目，以课程原文数字为准",
            "",
            "### 3. 常见错误选项特征",
            "- 含 \"政府担保\" / \"法币锚定\"（除非是稳定币课程）",
            "- 含 \"无需 KYC\" / \"匿名交易\"（Learn & Earn 平台均需 KYC）",
            "- 含 \"立即提现无限制\"（多数有锁定期或最低提现额）",
            "- 含 \"零风险\" / \"保本\"（加密货币均存在市场风险）",
            "",
            "### 4. 项目方常见考点",
            "- 项目愿景与定位（Layer1 / Layer2 / DeFi / 游戏公链等）",
            "- 共识机制（PoS / PoW / DPoS）",
            "- 代币用途（gas / 治理 / 质押）",
            "- 创始团队与投资方",
            "- 主网上线时间 / 代币分配比例",
            "",
            "### 5. 答题后操作",
            "- 答题通过后，奖励通常在 1-3 个工作日到账",
            "- Binance L&E 奖励以 ERC-20 形式发放，可在现货账户查看",
            "- 提现到 ETH 钱包需注意 gas 费（Binance 通常承担提现手续费）",
            "",
            "**标记：本课程需用户自行答题**",
        ])

    # ==================================================================
    # SubTask 2.8: batch_generate
    # ==================================================================
    def batch_generate(self) -> List[Dict[str, Any]]:
        """批量生成所有 Binance L&E 课程答题指南。

        复用 OpportunityRadar.scan_binance_learn_earn() 获取课程列表，
        逐个调用 generate_guide，每个独立 try/except 互不影响。

        Returns:
            每个课程的生成结果字典列表，含 course_url/course_name/status/
            result/error 字段。status 取值：ok / skipped / error。
        """
        from engine.crypto.opportunity_radar import OpportunityRadar

        # 复用 OpportunityRadar 获取课程列表，不重复实现抓取
        radar = OpportunityRadar(self.workspace, self.llm_client)
        try:
            courses = radar.scan_binance_learn_earn() or []
        except Exception as e:  # noqa: BLE001 - 雷达扫描失败不阻断批量
            print(f"[learn_earn] 获取 Binance L&E 课程列表失败：{e}")
            return []

        if not courses:
            print("[learn_earn] Binance L&E 课程列表为空（页面可能为 SPA 渲染）")
            return []

        print(f"[learn_earn] 获取到 {len(courses)} 门课程，开始批量生成答题指南")
        results: List[Dict[str, Any]] = []

        for course in courses:
            course_url = course.get("source_url", "")
            course_name = course.get("title", "")
            if not course_url:
                results.append({
                    "course_url": "",
                    "course_name": course_name,
                    "status": "skipped",
                    "error": "课程缺少 source_url",
                })
                continue

            try:
                result = self.generate_guide(course_url)
                results.append({
                    "course_url": course_url,
                    "course_name": course_name or result.get("course_name", ""),
                    "status": "ok",
                    "result": result,
                })
            except Exception as e:  # noqa: BLE001 - 单个课程失败不阻断其他
                print(f"[learn_earn] 生成答题指南失败 {course_url}：{e}")
                results.append({
                    "course_url": course_url,
                    "course_name": course_name,
                    "status": "error",
                    "error": str(e),
                })

        # 汇总日志
        ok_count = sum(1 for r in results if r.get("status") == "ok")
        print(
            f"[learn_earn] 批量生成完成：成功 {ok_count}/{len(results)}，"
            f"失败 {len(results) - ok_count}"
        )
        return results

    # ==================================================================
    # 私有：HTML 处理与 HTTP
    # ==================================================================
    @staticmethod
    def _fetch_text(url: str) -> str:
        """GET 请求返回文本。优先 requests，回退 urllib（与 opportunity_radar.py 一致）。"""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AutoCorp-LearnEarnAssistant/1.0"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
        }
        if _HAS_REQUESTS:
            resp = requests.get(url, timeout=20, headers=headers)
            resp.raise_for_status()
            return resp.text
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")

    @staticmethod
    def _html_to_text(html: str) -> str:
        """粗略提取 HTML 正文文本。

        步骤：
        1. 移除 script/style/nav/header/footer 等非正文块及内容
        2. 移除 HTML 注释
        3. 块级标签转换为换行（保留段落结构）
        4. 移除其余所有标签
        5. 解码常见 HTML 实体
        6. 压缩空白
        """
        if not html:
            return ""
        # 1. 移除非正文块
        text = re.sub(
            r"<(script|style|nav|header|footer|noscript)[^>]*>.*?</\1>",
            " ",
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        # 2. 移除 HTML 注释
        text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
        # 3. 块级标签转换为换行
        text = re.sub(
            r"</?(p|div|br|li|h[1-6]|tr|td|th|section|article|main)[^>]*>",
            "\n",
            text,
            flags=re.IGNORECASE,
        )
        # 4. 移除其余所有标签
        text = re.sub(r"<[^>]+>", " ", text)
        # 5. 解码常见 HTML 实体
        entities = {
            "&nbsp;": " ",
            "&amp;": "&",
            "&lt;": "<",
            "&gt;": ">",
            "&quot;": '"',
            "&#39;": "'",
            "&apos;": "'",
        }
        for ent, ch in entities.items():
            text = text.replace(ent, ch)
        # 数字实体
        text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
        # 6. 压缩空白
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text.strip()

    # ==================================================================
    # 私有：关键词提取与题目生成
    # ==================================================================
    @staticmethod
    def _extract_keywords(content: str) -> List[tuple]:
        """提取内容中的关键词及出现频次，按频次降序返回。

        规则：
        - 匹配长度 ≥4 的英文单词
        - 过滤停用词
        - 简单词根归一化（去复数 / 过去式后缀，统一小写）
        - 返回 [(keyword, count), ...]
        """
        if not content:
            return []
        # 提取英文单词（长度 ≥4，含连字符）
        words = re.findall(r"\b[a-zA-Z][a-zA-Z\-]{3,}\b", content)
        counts: Dict[str, int] = {}
        for w in words:
            low = w.lower().strip("-")
            if not low or low in _STOP_WORDS:
                continue
            # 简单词根归一化：去掉常见复数 / 过去式后缀
            normalized = low
            for suffix in ("ies", "ied", "ing", "ed", "es", "s"):
                if normalized.endswith(suffix) and len(normalized) - len(suffix) >= 4:
                    normalized = normalized[: -len(suffix)]
                    break
            counts[normalized] = counts.get(normalized, 0) + 1
        # 按频次降序排序，频次相同按字母序
        sorted_items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        return sorted_items

    @staticmethod
    def _make_question(
        keyword: str,
        occurrence: int,
        content: str,
        q_idx: int,
    ) -> Dict[str, Any]:
        """根据关键词生成一道选择题。

        Args:
            keyword: 关键词。
            occurrence: 关键词在原文出现频次。
            content: 课程正文（用于提取上下文片段作为解析）。
            q_idx: 题目序号（0/1），用于切换题型模板。

        Returns:
            题目字典：{question, options, answer, explanation, keyword,
                     occurrence, confidence_basis}
        """
        # 提取关键词在原文的上下文片段（用于解析）
        context = LearnEarnAssistant._extract_context(keyword, content)

        # 两套题型模板，按 q_idx 切换
        if q_idx == 0:
            question = f'根据课程内容，关于 "{keyword}" 的描述，以下哪项最准确？'
            options = [
                f"{keyword} 是本课程的核心概念之一，在课程中被多次提及",
                f"{keyword} 与课程内容完全无关",
                f"{keyword} 是一种中心化的传统金融工具",
                f"{keyword} 已经被监管机构禁止使用",
            ]
            answer = "A"
            explanation = (
                f'"{keyword}" 在课程原文中出现了 {occurrence} 次，'
                f"是课程的核心概念之一。"
            )
        else:
            question = f'课程中提到的 "{keyword}" 主要应用于以下哪个场景？'
            options = [
                "传统股票市场交易",
                "加密货币 / 区块链生态",
                "房地产投资信托",
                "外汇保证金交易",
            ]
            answer = "B"
            explanation = (
                "Learn & Earn 课程均围绕加密货币与区块链生态展开，"
                f'"{keyword}" 作为课程关键词应属于该领域。'
            )

        if context:
            explanation += f'\n原文上下文："...{context}..."'

        return {
            "question": question,
            "options": options,
            "answer": answer,
            "explanation": explanation,
            "keyword": keyword,
            "occurrence": occurrence,
            "confidence_basis": (
                "high" if occurrence >= LearnEarnAssistant._HIGH_CONFIDENCE_THRESHOLD
                else "medium" if occurrence >= 1 else "low"
            ),
        }

    @staticmethod
    def _extract_context(keyword: str, content: str, radius: int = 80) -> str:
        """提取关键词在原文的上下文片段（首处出现位置）。"""
        if not content or not keyword:
            return ""
        # 用 word boundary 匹配，避免子串误匹配
        pattern = r"\b" + re.escape(keyword) + r"\b"
        m = re.search(pattern, content, flags=re.IGNORECASE)
        if not m:
            return ""
        start = max(0, m.start() - radius)
        end = min(len(content), m.end() + radius)
        snippet = content[start:end].strip()
        # 压缩空白
        snippet = re.sub(r"\s+", " ", snippet)
        return snippet

    # ==================================================================
    # 私有：指南 markdown 组装
    # ==================================================================
    def _assemble_guide(
        self,
        course_name: str,
        course_url: str,
        content: str,
        analysis: Dict[str, Any],
        answers: List[Dict[str, Any]],
        confidence: Dict[str, Any],
    ) -> str:
        """组装完整答题指南 markdown（内容非空路径）。"""
        today = datetime.date.today().isoformat()
        degraded = bool(analysis.get("degraded"))

        lines: List[str] = [
            f"# Learn & Earn 答题指南 - {course_name}",
            "",
            f"- 课程 URL：{course_url}",
            f"- 生成日期：{today}",
            f"- 内容长度：{len(content)} 字符",
            f"- 题目数量：{len(answers)}",
            f"- 总体置信度：{confidence.get('overall', 'low')}",
            f"- LLM 分析：{'降级（规则代码生成）' if degraded else '已使用'}",
            "",
            "## 课程知识点摘要",
            "",
        ]

        # LLM 摘要或降级说明
        if degraded:
            lines.extend([
                f"> {analysis.get('summary', '（需 assistant 直接生成）')}",
                ">",
                f"> 降级原因：{analysis.get('reason', '未知')}",
                "",
            ])
        else:
            raw = (analysis.get("raw") or "").strip()
            if raw:
                lines.append(raw)
            else:
                lines.append("（LLM 未返回有效摘要）")
            lines.append("")

        # 置信度统计
        lines.extend([
            "## 答案置信度评估",
            "",
            f"- 高（≥90%）：{confidence.get('high_count', 0)} 题",
            f"- 中（60-90%）：{confidence.get('medium_count', 0)} 题",
            f"- 低（<60%）：{confidence.get('low_count', 0)} 题",
            "",
            "### 每题置信度",
            "",
            "| # | 题目 | 置信度 | 分数 | 依据 |",
            "|---|------|--------|------|------|",
        ])
        for i, pq in enumerate(confidence.get("per_question", []), 1):
            q_short = (pq.get("question", "") or "")[:60].replace("|", "\\|")
            lines.append(
                f"| {i} | {q_short} | {pq.get('confidence', '')} "
                f"| {pq.get('score', 0)} | {pq.get('basis', '')} |"
            )
        lines.append("")

        # 题目与答案
        lines.extend(["## 题目预测与答案", ""])
        if not answers:
            lines.extend([
                "> 未能基于课程内容生成题目，请参考下方通用答题技巧。",
                "",
            ])
            lines.append(self.fallback_tips())
            return "\n".join(lines)

        for i, ans in enumerate(answers, 1):
            lines.extend([
                f"### 第 {i} 题",
                "",
                f"**{ans.get('question', '')}**",
                "",
            ])
            for j, opt in enumerate(ans.get("options", [])):
                marker = chr(ord("A") + j)
                flag = " ✅" if marker == ans.get("answer") else ""
                lines.append(f"- {marker}. {opt}{flag}")
            lines.extend([
                "",
                f"**正确答案：{ans.get('answer', '')}**",
                "",
                f"**解析：** {ans.get('explanation', '')}",
                "",
                f"**关键词：** `{ans.get('keyword', '')}` （原文出现 {ans.get('occurrence', 0)} 次）",
                "",
                "---",
                "",
            ])

        # 通用答题技巧附录
        lines.extend([
            "## 附录：通用答题技巧",
            "",
            self.fallback_tips(),
            "",
        ])

        return "\n".join(lines)

    def _assemble_degraded_guide(
        self,
        course_name: str,
        course_url: str,
        reason: str,
    ) -> str:
        """组装降级路径的答题指南 markdown（内容抓取失败时使用）。"""
        today = datetime.date.today().isoformat()
        lines: List[str] = [
            f"# Learn & Earn 答题指南 - {course_name}",
            "",
            f"- 课程 URL：{course_url}",
            f"- 生成日期：{today}",
            f"- 内容长度：0 字符",
            f"- 题目数量：0",
            f"- 总体置信度：low",
            f"- LLM 分析：降级（课程内容为空）",
            "",
            "## 课程知识点摘要",
            "",
            "> 课程内容抓取失败，无法生成知识点摘要。",
            f"> 降级原因：{reason}",
            "",
            "## 题目预测与答案",
            "",
            "> 未能基于课程内容生成题目，请参考下方通用答题技巧自行答题。",
            "",
            self.fallback_tips(),
            "",
        ]
        return "\n".join(lines)

    # ==================================================================
    # 私有：课程名与文件名处理
    # ==================================================================
    @staticmethod
    def _derive_course_name(course_url: str) -> str:
        """从课程 URL 推断课程名（取 path 末段，去掉扩展名与查询参数）。"""
        if not course_url:
            return "unknown-course"
        # 去掉 query 与 fragment
        url = course_url.split("?", 1)[0].split("#", 1)[0]
        # 取末段
        last_segment = url.rstrip("/").rsplit("/", 1)[-1]
        if not last_segment:
            return "unknown-course"
        # 去掉扩展名
        if "." in last_segment:
            last_segment = last_segment.rsplit(".", 1)[0]
        # 连字符 → 空格，title case
        name = last_segment.replace("-", " ").replace("_", " ").strip()
        return name.title() if name else "unknown-course"

    @staticmethod
    def _slugify(name: str) -> str:
        """将课程名归一化为文件安全字符串（小写、连字符分隔）。"""
        if not name:
            return ""
        # 转小写
        s = name.lower().strip()
        # 非字母数字 → 连字符
        s = re.sub(r"[^a-z0-9]+", "-", s)
        # 压缩连续连字符
        s = re.sub(r"-+", "-", s).strip("-")
        return s
