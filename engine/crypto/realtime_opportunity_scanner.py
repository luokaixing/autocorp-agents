"""实时机会扫描器

实时验证 5 个平台（Layer3 / Galxe / Airdrops.io / Publish0x / DefiLlama Yields）
当日可访问性，聚合状态并产出 markdown 报告到
`company/knowledge/opportunities/realtime-scan-YYYY-MM-DD.md`。

设计要点：
- 诚实原则：抓取失败的平台在报告中标注"无法验证"，绝不编造状态或机会数。
- 优雅降级：每个平台独立 try/except，单个失败不影响其他平台扫描。
- 仅用 Python 标准库 urllib（不依赖第三方包），与 fetch_defi_realtime.py 风格一致。
- 文件即数据库：报告直接落盘到 company/knowledge/opportunities/。
"""
from __future__ import annotations

import datetime
import logging
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


# 项目根目录（engine/crypto/realtime_opportunity_scanner.py → 上溯两级即项目根）
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 报告输出目录
_OUTPUT_DIR = _PROJECT_ROOT / "company" / "knowledge" / "opportunities"

# 公共请求头（与 fetch_defi_realtime.py 风格一致）
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AutoCorp-RealtimeScanner/1.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
}

# 请求超时（秒）
_REQUEST_TIMEOUT = 20

# ------------------------------------------------------------------
# 行业利润池定位（industry_profit_pool_position）取值
# ------------------------------------------------------------------
# high-profit-chain: 切入最挣钱行业价值链（最高优先级）
# mid:               中等利润行业
# low-red-ocean:     低附加值红海（最低优先级）
_PROFIT_POOL_HIGH = "high-profit-chain"
_PROFIT_POOL_MID = "mid"
_PROFIT_POOL_LOW = "low-red-ocean"

# 利润池定位排序权重（值越小越靠前）
_PROFIT_POOL_ORDER: Dict[str, int] = {
    _PROFIT_POOL_HIGH: 0,
    _PROFIT_POOL_MID: 1,
    _PROFIT_POOL_LOW: 2,
}

# 赛道类别 → 行业利润池定位映射
# 用于为现有平台扫描结果标注利润池定位字段
_TRACK_CATEGORY_PROFIT_POOL: Dict[str, str] = {
    # 加密平台：竞争激烈、低附加值环节 → 红海
    "crypto": _PROFIT_POOL_LOW,
    "us-crypto": _PROFIT_POOL_LOW,
    # 联盟营销 / 微任务：低附加值 → 红海
    "affiliate": _PROFIT_POOL_LOW,
    "us-affiliate": _PROFIT_POOL_LOW,
    "us-microtask": _PROFIT_POOL_LOW,
    # 内容服务 / 数字产品 / 自动化代运营 / 自由职业 / 开发者社区：中等利润
    "content-service": _PROFIT_POOL_MID,
    "digital-product": _PROFIT_POOL_MID,
    "automation-service": _PROFIT_POOL_MID,
    "us-freelance": _PROFIT_POOL_MID,
    "us-content": _PROFIT_POOL_MID,
    "us-dev": _PROFIT_POOL_MID,
    "us-digital-product": _PROFIT_POOL_MID,
}


class RealtimeOpportunityScanner:
    """实时机会扫描器：验证多平台可访问性并产出当日扫描报告。

    使用方式：
        scanner = RealtimeOpportunityScanner()
        results = scanner.scan_all()         # 验证 5 个平台
        report_path = scanner.generate_report()  # 写入 markdown 报告
    """

    def __init__(self) -> None:
        """初始化扫描器，设置 5 个扫描目标 URL 列表。

        每个目标包含：平台名 / URL / 预期收益 / 启动门槛（用于报告展示，
        数值来自历史 spec，非实时抓取数据）。
        """
        # 5 个平台扫描目标（顺序即报告展示顺序）
        self.targets: List[Dict[str, str]] = [
            {
                "platform": "Layer3",
                "url": "https://app.layer3.xyz/discover",
                "expected_reward": "CUBE 积分 → 空投（$5-200）",
                "entry_barrier": "注册 Layer3 + 连接钱包（零成本）",
            },
            {
                "platform": "Galxe",
                "url": "https://galxe.com",
                "expected_reward": "OAT / 积分 → 空投（$2-100）",
                "entry_barrier": "注册 Galxe + 连接钱包 / Twitter（零成本）",
            },
            {
                "platform": "Airdrops.io",
                "url": "https://airdrops.io/latest/",
                "expected_reward": "代币空投（$10-500，概率性）",
                "entry_barrier": "按各项目要求（多数为零成本测试网交互）",
            },
            {
                "platform": "Publish0x",
                "url": "https://publish0x.com",
                "expected_reward": "内容打赏（$0.01-5 / 篇，立即到账）",
                "entry_barrier": "注册 Publish0x（零成本，无需钱包初始资金）",
            },
            {
                "platform": "DefiLlama Yields",
                "url": "https://defillama.com/yields",
                "expected_reward": "DeFi 收益数据参考（信息源，非直接收益）",
                "entry_barrier": "无需注册（数据展示页）",
            },
        ]

        # 非加密赛道扫描目标（按赛道分组，顺序即报告展示顺序）
        # track_category 取值：content-service / affiliate / digital-product / automation-service
        self.non_crypto_targets: List[Dict[str, str]] = [
            # —— 内容服务赛道（content-service）—— AI 内容外包 + 技术写作社区
            {
                "platform": "Fiverr",
                "track_category": "content-service",
                "url": "https://www.fiverr.com",
                "notes": "AI 内容外包平台，海外自由职业零工市场",
            },
            {
                "platform": "Upwork",
                "track_category": "content-service",
                "url": "https://www.upwork.com",
                "notes": "AI 内容外包平台，海外长期合约市场",
            },
            {
                "platform": "猪八戒",
                "track_category": "content-service",
                "url": "https://www.zbj.com",
                "notes": "AI 内容外包平台，国内众包服务市场",
            },
            {
                "platform": "闲鱼",
                "track_category": "content-service",
                "url": "https://www.goofish.com",
                "notes": "AI 内容外包平台，国内二手 + 服务交易",
            },
            # 技术写作赛道（content-service 子类）
            {
                "platform": "dev.to",
                "track_category": "content-service",
                "url": "https://dev.to",
                "notes": "技术写作社区，流量分成 + 品牌曝光",
            },
            {
                "platform": "Hashnode",
                "track_category": "content-service",
                "url": "https://hashnode.com",
                "notes": "技术写作社区，开发者博客托管平台",
            },
            {
                "platform": "Medium",
                "track_category": "content-service",
                "url": "https://medium.com",
                "notes": "技术写作社区，Partner Program 收益分成",
            },
            # —— 联盟营销赛道（affiliate）——
            {
                "platform": "Amazon Associates",
                "track_category": "affiliate",
                "url": "https://affiliate-program.amazon.com",
                "notes": "联盟营销，亚马逊商品分销分成",
            },
            {
                "platform": "Awin",
                "track_category": "affiliate",
                "url": "https://www.awin.com",
                "notes": "联盟营销，ShareASale 已并入 Awin",
            },
            {
                "platform": "淘宝联盟",
                "track_category": "affiliate",
                "url": "https://pub.alimama.com",
                "notes": "联盟营销，阿里妈妈淘宝客分销",
            },
            # —— 数字产品赛道（digital-product）——
            {
                "platform": "Notion 模板市场",
                "track_category": "digital-product",
                "url": "https://www.notion.so/templates",
                "notes": "数字产品销售，Notion 模板上架分发",
            },
            {
                "platform": "Obsidian 插件",
                "track_category": "digital-product",
                "url": "https://obsidian.md/plugins",
                "notes": "数字产品销售，Obsidian 社区插件发布",
            },
            {
                "platform": "Gumroad",
                "track_category": "digital-product",
                "url": "https://gumroad.com",
                "notes": "数字产品销售，独立创作者电商",
            },
            # —— 自动化代运营赛道（automation-service）——
            {
                "platform": "小红书",
                "track_category": "automation-service",
                "url": "https://www.xiaohongshu.com",
                "notes": "自动化代运营，种草内容矩阵",
            },
            {
                "platform": "微信公众号",
                "track_category": "automation-service",
                "url": "https://mp.weixin.qq.com",
                "notes": "自动化代运营，公众号矩阵",
            },
            {
                "platform": "抖音",
                "track_category": "automation-service",
                "url": "https://www.douyin.com",
                "notes": "自动化代运营，短视频矩阵",
            },
        ]

        # 美国市场扫描目标（按赛道分组，顺序即报告展示顺序）
        # track_category 取值：us-freelance / us-content / us-dev /
        # us-digital-product / us-microtask / us-affiliate / us-crypto
        self.us_market_targets: List[Dict[str, str]] = [
            # —— 美国自由职业赛道（us-freelance）——
            {
                "platform": "Upwork",
                "track_category": "us-freelance",
                "url": "https://www.upwork.com",
                "notes": "美国自由职业平台，长期合约 + 时薪项目",
            },
            {
                "platform": "Fiverr",
                "track_category": "us-freelance",
                "url": "https://www.fiverr.com",
                "notes": "美国自由职业平台，零工任务市场",
            },
            {
                "platform": "Contra",
                "track_category": "us-freelance",
                "url": "https://contra.com",
                "notes": "美国自由职业平台，零佣金独立工作者社区",
            },
            {
                "platform": "Toptal",
                "track_category": "us-freelance",
                "url": "https://www.toptal.com",
                "notes": "美国自由职业平台，高端人才精选招聘",
            },
            # —— 美国内容创作赛道（us-content）——
            {
                "platform": "Medium",
                "track_category": "us-content",
                "url": "https://medium.com",
                "notes": "美国内容创作平台，Partner Program 收益分成",
            },
            {
                "platform": "Substack",
                "track_category": "us-content",
                "url": "https://substack.com",
                "notes": "美国内容创作平台，付费订阅邮件 newsletter",
            },
            {
                "platform": "Vocal.media",
                "track_category": "us-content",
                "url": "https://vocal.media",
                "notes": "美国内容创作平台，故事创作奖金分成",
            },
            {
                "platform": "HubPages",
                "track_category": "us-content",
                "url": "https://hubpages.com",
                "notes": "美国内容创作平台，广告分成博客",
            },
            {
                "platform": "NewsBreak",
                "track_category": "us-content",
                "url": "https://www.newsbreak.com",
                "notes": "美国内容创作平台，本地新闻创作者计划",
            },
            # —— 美国开发者社区赛道（us-dev）——
            {
                "platform": "dev.to",
                "track_category": "us-dev",
                "url": "https://dev.to",
                "notes": "美国开发者社区，技术写作流量分成",
            },
            {
                "platform": "Hashnode",
                "track_category": "us-dev",
                "url": "https://hashnode.com",
                "notes": "美国开发者社区，开发者博客托管平台",
            },
            # —— 美国数字产品赛道（us-digital-product）——
            {
                "platform": "Gumroad",
                "track_category": "us-digital-product",
                "url": "https://gumroad.com",
                "notes": "美国数字产品销售，独立创作者电商",
            },
            {
                "platform": "Etsy",
                "track_category": "us-digital-product",
                "url": "https://www.etsy.com",
                "notes": "美国数字产品销售，手作 + 数字商品市场",
            },
            {
                "platform": "Notion 模板市场",
                "track_category": "us-digital-product",
                "url": "https://www.notion.so/templates",
                "notes": "美国数字产品销售，Notion 模板上架分发",
            },
            {
                "platform": "Teachers Pay Teachers",
                "track_category": "us-digital-product",
                "url": "https://www.teacherspayteachers.com",
                "notes": "美国数字产品销售，教师课件交易市场",
            },
            # —— 美国测试/调研/微任务赛道（us-microtask）——
            {
                "platform": "UserTesting",
                "track_category": "us-microtask",
                "url": "https://www.usertesting.com",
                "notes": "美国微任务平台，网站 / App 可用性测试",
            },
            {
                "platform": "Prolific",
                "track_category": "us-microtask",
                "url": "https://www.prolific.com",
                "notes": "美国微任务平台，学术调研参与者招募",
            },
            {
                "platform": "MTurk",
                "track_category": "us-microtask",
                "url": "https://www.mturk.com",
                "notes": "美国微任务平台，Amazon 众包任务市场",
            },
            {
                "platform": "Clickworker",
                "track_category": "us-microtask",
                "url": "https://www.clickworker.com",
                "notes": "美国微任务平台，AI 训练数据标注",
            },
            {
                "platform": "Branded Surveys",
                "track_category": "us-microtask",
                "url": "https://www.brandedsurveys.com",
                "notes": "美国微任务平台，付费问卷调研",
            },
            # —— 美国联盟营销赛道（us-affiliate）——
            {
                "platform": "Amazon Associates US",
                "track_category": "us-affiliate",
                "url": "https://affiliate-program.amazon.com",
                "notes": "美国联盟营销，亚马逊商品分销分成",
            },
            {
                "platform": "Impact",
                "track_category": "us-affiliate",
                "url": "https://impact.com",
                "notes": "美国联盟营销，全栈联盟营销管理平台",
            },
            {
                "platform": "ShareASale",
                "track_category": "us-affiliate",
                "url": "https://www.shareasale.com",
                "notes": "美国联盟营销，商家与发布者对接平台",
            },
            # —— 美国加密赛道（us-crypto）——
            {
                "platform": "Coinbase Earn",
                "track_category": "us-crypto",
                "url": "https://www.coinbase.com/earn",
                "notes": "美国加密平台，学习赚币 + 空投任务",
            },
            {
                "platform": "Layer3",
                "track_category": "us-crypto",
                "url": "https://layer3.xyz",
                "notes": "美国加密平台，链上任务 + CUBE 积分空投",
            },
            {
                "platform": "Galxe",
                "track_category": "us-crypto",
                "url": "https://galxe.com",
                "notes": "美国加密平台，Web3 任务 + OAT 凭证空投",
            },
        ]

        # 报告输出目录
        self.output_dir: Path = _OUTPUT_DIR

        # 确保输出目录存在（失败不阻断 import）
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:  # noqa: BLE001
            logger.warning("输出目录创建失败: %s — %s", self.output_dir, e)

        # 缓存最近一次 scan_all 结果（generate_report 复用）
        self._last_scan: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def verify(self, url: str) -> Dict[str, Any]:
        """WebFetch 验证 URL 当日可访问性。

        用 urllib.request 抓取目标 URL，返回包含状态码、可访问性、抓取耗时
        与错误信息的字典。所有网络异常用 try/except 兜底，绝不抛出。

        Args:
            url: 待验证的 URL（含 scheme）。

        Returns:
            dict: {
                url, status_code, accessible, fetch_time, error
            }
            - status_code: HTTP 状态码（int），失败时为 0
            - accessible: bool，状态码 200-399 视为可访问
            - fetch_time: 抓取耗时（秒，float）
            - error: 错误信息字符串，成功时为空字符串
        """
        result: Dict[str, Any] = {
            "url": url,
            "status_code": 0,
            "accessible": False,
            "fetch_time": 0.0,
            "error": "",
        }

        start = datetime.datetime.now()
        try:
            req = urllib.request.Request(url, headers=_HEADERS, method="GET")
            with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT) as resp:
                status_code = int(getattr(resp, "status", 0) or 0)
                # 读取响应以确认连接完整（不保留正文）
                try:
                    resp.read()
                except Exception as read_err:  # noqa: BLE001 - 读取失败但状态码已知
                    logger.debug("响应体读取失败 %s: %s", url, read_err)
                result["status_code"] = status_code
                result["accessible"] = 200 <= status_code < 400
        except urllib.error.HTTPError as e:
            # HTTPError 仍携带状态码（如 403/404）
            result["status_code"] = int(e.code or 0)
            # 4xx 在某些站点表示反爬但页面实际可访问，仍判定为"可达但被拦截"
            result["accessible"] = 200 <= result["status_code"] < 400
            result["error"] = f"HTTPError {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            result["error"] = f"URLError: {e.reason}"
        except TimeoutError as e:
            result["error"] = f"TimeoutError: {e}"
        except Exception as e:  # noqa: BLE001 - 兜底所有未知异常
            result["error"] = f"{type(e).__name__}: {e}"
        finally:
            elapsed = (datetime.datetime.now() - start).total_seconds()
            result["fetch_time"] = round(elapsed, 3)

        return result

    def scan_all(self) -> List[Dict[str, Any]]:
        """聚合加密 + 国内非加密 + 美国市场 + 最挣钱行业价值链切入扫描结果。

        依次对：
        - self.targets（加密，5 个平台，market_region="global"）
        - self.non_crypto_targets（国内非加密，4 类赛道 16 个平台，market_region="cn"）
        - self.us_market_targets（美国市场，7 类赛道 26 个平台，market_region="us"）
        - scan_value_chain_entry_opportunities()（最挣钱行业价值链切入点）
        中的每个目标调用 verify() / 基线数据，合并平台元信息与验证结果。
        每个平台独立 try/except，单个失败不影响其他平台。

        所有结果均带以下字段：
        - `track_category`：赛道类别（crypto / content-service / affiliate /
          digital-product / automation-service / us-freelance / us-content /
          us-dev / us-digital-product / us-microtask / us-affiliate / us-crypto /
          value-chain-entry）
        - `market_region`：市场区域（"global" / "cn" / "us"）
        - `prescreen_status`：竞争力预筛状态（"not_screened" 默认值，预筛需
          人工或 CEO agent 判断）
        - `industry_profit_pool_position`：行业利润池定位
          （"high-profit-chain" / "mid" / "low-red-ocean"）

        排序逻辑（按"是否切入最挣钱行业"优先排序）：
        - high-profit-chain（切入最挣钱行业价值链）排最前
        - mid（中等利润行业）排中间
        - low-red-ocean（低附加值红海）排最后
        同一档内保持原有扫描顺序（稳定排序）。

        Returns:
            list[dict]: 每个平台/切入点一个字典。加密平台字段：
                platform, track_category, market_region, prescreen_status,
                accessible, status, opportunities_count, fetch_time, url,
                expected_reward, entry_barrier, status_code, error,
                industry_profit_pool_position
            - status: "accessible" / "inaccessible" / "unverified" /
              "opportunity"（价值链切入点）
            - opportunities_count: 仅作展示用途，不实时解析页面，固定为
              "未解析"（HTML 解析机会数不可靠，本扫描器只验证可访问性，
              避免编造数据）
            国内非加密平台字段详见 scan_non_crypto_tracks() 文档。
            美国市场平台字段详见 scan_us_market_tracks() 文档。
            价值链切入点字段详见 scan_value_chain_entry_opportunities() 文档。
        """
        # —— 加密赛道扫描（向后兼容：保留原有 5 平台逻辑）——
        # 加密无国界，market_region 统一标记为 "global"
        results: List[Dict[str, Any]] = []
        for target in self.targets:
            platform = target["platform"]
            url = target["url"]
            try:
                verify_result = self.verify(url)
            except Exception as e:  # noqa: BLE001 - 双重保险
                verify_result = {
                    "url": url,
                    "status_code": 0,
                    "accessible": False,
                    "fetch_time": 0.0,
                    "error": f"{type(e).__name__}: {e}",
                }

            # 状态文案
            if verify_result["accessible"]:
                status = "accessible"
            elif verify_result["error"]:
                status = "unverified"
            else:
                status = "inaccessible"

            entry: Dict[str, Any] = {
                "platform": platform,
                # 赛道类别：加密平台统一标记
                "track_category": "crypto",
                # 市场区域：加密无国界
                "market_region": "global",
                # 竞争力预筛状态：默认未筛（需人工 / CEO agent 判断）
                "prescreen_status": "not_screened",
                "accessible": verify_result["accessible"],
                "status": status,
                # 机会数不实时解析（避免编造），仅标注
                "opportunities_count": "未解析（仅验证可访问性）",
                "fetch_time": verify_result["fetch_time"],
                "url": url,
                "expected_reward": target["expected_reward"],
                "entry_barrier": target["entry_barrier"],
                "status_code": verify_result["status_code"],
                "error": verify_result["error"],
            }
            results.append(entry)
            logger.info(
                "scan_all[crypto]: %s -> %s (HTTP %s, %.3fs)",
                platform,
                status,
                verify_result["status_code"],
                verify_result["fetch_time"],
            )

        # —— 国内非加密赛道扫描（扩展：内容服务 / 联盟营销 / 数字产品 / 自动化代运营）——
        try:
            non_crypto_results = self.scan_non_crypto_tracks()
        except Exception as e:  # noqa: BLE001 - 非加密扫描整体失败不阻断加密结果
            logger.error("scan_non_crypto_tracks 整体失败，仅返回加密结果: %s", e)
            non_crypto_results = []
        results.extend(non_crypto_results)

        # —— 美国市场赛道扫描（扩展：自由职业 / 内容创作 / 开发者社区 /
        #     数字产品 / 微任务 / 联盟营销 / 加密 共 7 类赛道）——
        try:
            us_market_results = self.scan_us_market_tracks()
        except Exception as e:  # noqa: BLE001 - 美国市场扫描整体失败不阻断前两层结果
            logger.error("scan_us_market_tracks 整体失败，仅返回加密 + 国内非加密结果: %s", e)
            us_market_results = []
        results.extend(us_market_results)

        # —— 为现有平台扫描结果标注行业利润池定位 ——
        # 按 track_category 映射到 high-profit-chain / mid / low-red-ocean
        for entry in results:
            track_cat = entry.get("track_category", "")
            entry["industry_profit_pool_position"] = _TRACK_CATEGORY_PROFIT_POOL.get(
                track_cat, _PROFIT_POOL_MID
            )

        # —— 最挣钱行业价值链切入点扫描（Task 7 新增）——
        # 价值链切入点 profit_pool_position = high-profit-chain，排最前
        try:
            value_chain_entries = self.scan_value_chain_entry_opportunities()
        except Exception as e:  # noqa: BLE001 - 价值链扫描失败不阻断前三层结果
            logger.error("scan_value_chain_entry_opportunities 整体失败: %s", e)
            value_chain_entries = []

        for vc in value_chain_entries:
            # 适配为与平台扫描结果兼容的格式，便于统一报告与排序
            adapted: Dict[str, Any] = dict(vc)
            adapted["platform"] = (
                f"[价值链切入] {vc.get('industry', '')}: {vc.get('chain_segment', '')}"
            )
            adapted["track_category"] = "value-chain-entry"
            adapted["market_region"] = "global"
            adapted["prescreen_status"] = "not_screened"
            adapted["accessible"] = True
            adapted["status"] = "opportunity"
            adapted["opportunities_count"] = "价值链切入点（基线数据）"
            adapted["fetch_time"] = 0.0
            adapted["url"] = ""
            adapted["expected_reward"] = vc.get("time_to_revenue", "")
            adapted["entry_barrier"] = vc.get("barrier_analysis", "")
            adapted["status_code"] = 0
            adapted["error"] = ""
            adapted["industry_profit_pool_position"] = _PROFIT_POOL_HIGH
            results.append(adapted)
            logger.info(
                "scan_all[value-chain]: %s -> %s",
                adapted["platform"],
                vc.get("entry_type", ""),
            )

        # —— 按"是否切入最挣钱行业"优先排序（稳定排序）——
        # high-profit-chain (0) < mid (1) < low-red-ocean (2)
        # Python sort 默认稳定，同一档内保持原有扫描顺序
        results.sort(
            key=lambda r: _PROFIT_POOL_ORDER.get(
                r.get("industry_profit_pool_position", _PROFIT_POOL_MID),
                _PROFIT_POOL_ORDER[_PROFIT_POOL_MID],
            )
        )

        self._last_scan = results
        return results

    def scan_non_crypto_tracks(self) -> List[Dict[str, Any]]:
        """扫描国内非加密赛道平台当日可访问性。

        覆盖 4 类非加密赛道：
        - 内容服务（content-service）：Fiverr / Upwork / 猪八戒 / 闲鱼 /
          dev.to / Hashnode / Medium
        - 联盟营销（affiliate）：Amazon Associates / Awin / 淘宝联盟
        - 数字产品（digital-product）：Notion 模板 / Obsidian 插件 / Gumroad
        - 自动化代运营（automation-service）：小红书 / 微信公众号 / 抖音

        每个平台独立 try/except，单个失败不影响其他平台（优雅降级）。
        状态文案区分超时与一般错误，便于后续分流处理。

        所有结果均带 `market_region="cn"`（国内市场）与
        `prescreen_status="not_screened"`（默认未预筛，需人工 / CEO agent 判断）。

        Returns:
            list[dict]: 每个平台一个字典，字段：
                platform, track_category, market_region, prescreen_status,
                url, accessible, status, status_code, fetch_time, notes
            - status: "accessible" / "timeout" / "error"
            - notes: 平台说明（赛道定位 / 收益模式）
        """
        results: List[Dict[str, Any]] = []
        for target in self.non_crypto_targets:
            platform = target["platform"]
            url = target["url"]
            try:
                verify_result = self.verify(url)
            except Exception as e:  # noqa: BLE001 - 双重保险
                verify_result = {
                    "url": url,
                    "status_code": 0,
                    "accessible": False,
                    "fetch_time": 0.0,
                    "error": f"{type(e).__name__}: {e}",
                }

            # 状态文案（区分超时与一般错误）
            err_text = verify_result.get("error", "") or ""
            if verify_result["accessible"]:
                status = "accessible"
            elif "timeout" in err_text.lower() or "TimeoutError" in err_text:
                status = "timeout"
            else:
                status = "error"

            entry: Dict[str, Any] = {
                "platform": platform,
                "track_category": target["track_category"],
                # 市场区域：国内非加密平台统一标记为 "cn"
                "market_region": "cn",
                # 竞争力预筛状态：默认未筛（需人工 / CEO agent 判断）
                "prescreen_status": "not_screened",
                "url": url,
                "accessible": verify_result["accessible"],
                "status": status,
                "status_code": verify_result["status_code"],
                "fetch_time": verify_result["fetch_time"],
                "notes": target["notes"],
            }
            results.append(entry)
            logger.info(
                "scan_non_crypto[%s]: %s -> %s (HTTP %s, %.3fs)",
                target["track_category"],
                platform,
                status,
                verify_result["status_code"],
                verify_result["fetch_time"],
            )
        return results

    def scan_us_market_tracks(self) -> List[Dict[str, Any]]:
        """扫描美国市场平台当日可访问性。

        覆盖 7 类美国市场赛道：
        - 自由职业（us-freelance）：Upwork / Fiverr / Contra / Toptal
        - 内容创作（us-content）：Medium / Substack / Vocal.media / HubPages /
          NewsBreak
        - 开发者社区（us-dev）：dev.to / Hashnode
        - 数字产品（us-digital-product）：Gumroad / Etsy / Notion 模板市场 /
          Teachers Pay Teachers
        - 测试/调研/微任务（us-microtask）：UserTesting / Prolific / MTurk /
          Clickworker / Branded Surveys
        - 联盟营销（us-affiliate）：Amazon Associates US / Impact / ShareASale
        - 加密（us-crypto）：Coinbase Earn / Layer3 / Galxe

        每个平台独立 try/except，单个失败不影响其他平台（优雅降级）。
        状态文案区分超时与一般错误，与 scan_non_crypto_tracks() 风格一致。

        所有结果均带 `market_region="us"`（美国市场）与
        `prescreen_status="not_screened"`（默认未预筛，预筛需人工或 CEO agent
        判断）。

        Returns:
            list[dict]: 每个平台一个字典，字段：
                platform, track_category, market_region, url, accessible,
                status, status_code, fetch_time, prescreen_status, notes
            - status: "accessible" / "timeout" / "error"
            - notes: 平台说明（赛道定位 / 收益模式）
        """
        results: List[Dict[str, Any]] = []
        for target in self.us_market_targets:
            platform = target["platform"]
            url = target["url"]
            try:
                verify_result = self.verify(url)
            except Exception as e:  # noqa: BLE001 - 双重保险
                verify_result = {
                    "url": url,
                    "status_code": 0,
                    "accessible": False,
                    "fetch_time": 0.0,
                    "error": f"{type(e).__name__}: {e}",
                }

            # 状态文案（区分超时与一般错误）
            err_text = verify_result.get("error", "") or ""
            if verify_result["accessible"]:
                status = "accessible"
            elif "timeout" in err_text.lower() or "TimeoutError" in err_text:
                status = "timeout"
            else:
                status = "error"

            entry: Dict[str, Any] = {
                "platform": platform,
                "track_category": target["track_category"],
                # 市场区域：美国市场平台统一标记为 "us"
                "market_region": "us",
                "url": url,
                "accessible": verify_result["accessible"],
                "status": status,
                "status_code": verify_result["status_code"],
                "fetch_time": verify_result["fetch_time"],
                # 竞争力预筛状态：默认未筛（需人工 / CEO agent 判断）
                "prescreen_status": "not_screened",
                "notes": target["notes"],
            }
            results.append(entry)
            logger.info(
                "scan_us_market[%s]: %s -> %s (HTTP %s, %.3fs)",
                target["track_category"],
                platform,
                status,
                verify_result["status_code"],
                verify_result["fetch_time"],
            )
        return results

    # ------------------------------------------------------------------
    # 最挣钱行业扫描（Task 7 新增）
    # ------------------------------------------------------------------

    def scan_most_profitable_industries(self) -> List[Dict[str, Any]]:
        """扫描 2026 年最挣钱行业及其利润数据。

        返回行业列表（按利润率 × 增长率 × AI 可切入性综合排序），
        每个行业包含 8 要素：利润规模 / 利润率 / 增长率 / 利润池分布 /
        进入壁垒 / AI 公司可切入性 / 3 个机会点 / 风险。

        优雅降级：行业利润数据基于公开权威来源整理的基线数据集（非实时
        抓取，因行业利润数据无单一可靠 API），数据源 URL 一并列出供人工
        复核。网络验证失败不影响基线数据返回。

        Returns:
            list[dict]: 每个行业一个字典，字段：
                industry_name, profit_scale, profit_margin, growth_rate,
                profit_pool_distribution, entry_barrier,
                ai_company_accessible, opportunity_points, risks,
                data_sources, scanned_at
            - ai_company_accessible: dict，含 accessible(bool) 与 reason(str)
            - profit_pool_distribution: dict，价值链各环节利润占比
            - opportunity_points: list[str]，3 个具体机会点
            - data_sources: list[str]，数据来源 URL 列表
        """
        logger.info("scan_most_profitable_industries: 开始扫描最挣钱行业")
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        industries = self._get_curated_industries()
        results: List[Dict[str, Any]] = []
        for ind in industries:
            entry = dict(ind)  # 浅拷贝，避免修改基线数据
            entry["scanned_at"] = timestamp
            results.append(entry)
        logger.info(
            "scan_most_profitable_industries: 完成，共 %d 个行业", len(results)
        )
        return results

    def scan_value_chain_entry_opportunities(
        self, industry_name: str = None
    ) -> List[Dict[str, Any]]:
        """针对最挣钱行业识别价值链切入点。

        对每个行业（或指定行业）生成 3 个价值链切入机会点，切入点类型
        覆盖：efficiency_tool / content_support / data_service / automation /
        marketing_support。

        优雅降级：行业名不存在时返回空列表，不抛异常。

        Args:
            industry_name: 指定行业名；None 则扫描所有 Top 行业。

        Returns:
            list[dict]: 每个切入点一个字典，字段：
                industry, chain_segment, entry_type, description,
                target_customer, value_proposition, barrier_analysis,
                startup_cost, time_to_revenue, sustainability,
                resource_match, profit_pool_position, scanned_at
            - entry_type: efficiency_tool / content_support / data_service /
              automation / marketing_support
            - sustainability: asset（一次投入持续产出） / service（做一次赚一次）
            - profit_pool_position: high-profit-chain（切入最挣钱行业价值链）
        """
        logger.info(
            "scan_value_chain_entry_opportunities: industry_name=%s",
            industry_name or "(全部)",
        )
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        curated = self._get_curated_value_chain_entries()
        results: List[Dict[str, Any]] = []
        for entry in curated:
            if industry_name and entry["industry"] != industry_name:
                continue
            item = dict(entry)
            item["scanned_at"] = timestamp
            results.append(item)
        logger.info(
            "scan_value_chain_entry_opportunities: 完成，共 %d 个切入点",
            len(results),
        )
        return results

    # ------------------------------------------------------------------
    # 私有：最挣钱行业基线数据（基于公开权威来源整理）
    # ------------------------------------------------------------------

    @staticmethod
    def _get_curated_industries() -> List[Dict[str, Any]]:
        """返回 2026 年最挣钱行业基线数据集。

        数据基于 Statista / McKinsey / BCG / 行业报告等公开来源整理，
        每个行业的 data_sources 字段列出原始来源 URL 供人工复核。
        遵循诚实原则：数据为基线估算而非实时抓取，仅供战略参考。
        """
        return [
            {
                "industry_name": "AI 应用层（垂直 SaaS / Agent 平台 / Coding 助手）",
                "profit_scale": "$1500B+（2026 全球 AI 应用市场）",
                "profit_margin": "70-90%（SaaS 毛利率）",
                "growth_rate": "50-80% YoY",
                "profit_pool_distribution": {
                    "垂直 SaaS": "40%",
                    "Agent 平台": "25%",
                    "Coding 助手": "20%",
                    "其他工具": "15%",
                },
                "entry_barrier": "中（需产品能力 + 行业 know-how + 分发渠道）",
                "ai_company_accessible": {
                    "accessible": True,
                    "reason": "垂直 SaaS / 工具环节适合 AI 公司切入，"
                    "复用已有 LLM 能力与浏览器自动化能力",
                },
                "opportunity_points": [
                    "垂直行业 AI 工具（法律 / 医疗 / 财税文档自动化）",
                    "Agent 模板市场（销售 / 客服 / 数据分析 Agent）",
                    "AI Coding 辅助工具（代码审查 / 测试生成）",
                ],
                "risks": "巨头竞争 / 技术迭代快 / 用户留存难",
                "data_sources": [
                    "https://www.statista.com/outlook/technology/artificial-intelligence",
                    "https://www.mckinsey.com/capabilities/quantumblack/our-insights",
                ],
            },
            {
                "industry_name": "AI 基础设施与算力（GPU 云 / 推理服务 / 模型托管）",
                "profit_scale": "$200B+（2026 全球 AI 基础设施市场）",
                "profit_margin": "60-80%（云厂商毛利率）",
                "growth_rate": "40-60% YoY",
                "profit_pool_distribution": {
                    "算力租赁": "45%",
                    "模型托管": "25%",
                    "推理服务": "20%",
                    "工具链": "10%",
                },
                "entry_barrier": "高（需 GPU 集群 / 数据中心 / 大额资本投入）",
                "ai_company_accessible": {
                    "accessible": False,
                    "reason": "核心算力环节资本密集，AI 公司无法切入；"
                    "但工具链 / 监控 / 成本优化环节可切入",
                },
                "opportunity_points": [
                    "GPU 算力价格聚合与比价工具",
                    "模型推理成本监控仪表板",
                    "AI 基础设施教程与对比内容",
                ],
                "risks": "资本密集 / 巨头垄断 / 技术迭代快",
                "data_sources": [
                    "https://www.statista.com/outlook/technology/cloud-computing",
                    "https://www.mckinsey.com/industries/technology-media-and-telecommunications/our-insights",
                ],
            },
            {
                "industry_name": "企业服务 SaaS（垂直行业 SaaS / 开发者工具）",
                "profit_scale": "$300B+（2026 全球 SaaS 市场）",
                "profit_margin": "70-85%",
                "growth_rate": "20-30% YoY",
                "profit_pool_distribution": {
                    "垂直行业 SaaS": "45%",
                    "开发者工具": "25%",
                    "协作工具": "20%",
                    "其他": "10%",
                },
                "entry_barrier": "中（需产品能力 + 分发渠道 + 集成生态）",
                "ai_company_accessible": {
                    "accessible": True,
                    "reason": "垂直工具 / 集成中间件 / 内容环节适合 AI 公司切入",
                },
                "opportunity_points": [
                    "SaaS 工具对比与选型平台",
                    "垂直行业工作流自动化模板",
                    "SaaS 集成 API 适配器",
                ],
                "risks": "巨头竞争 / 获客成本高 / 流失率高",
                "data_sources": [
                    "https://www.statista.com/outlook/technology/software",
                    "https://www.bcg.com/industries/technology-industry",
                ],
            },
            {
                "industry_name": "金融科技（支付 / 嵌入式金融 / 保险科技）",
                "profit_scale": "$200B+（2026 全球金融科技利润）",
                "profit_margin": "30-60%",
                "growth_rate": "20-30% YoY",
                "profit_pool_distribution": {
                    "支付": "35%",
                    "嵌入式金融": "25%",
                    "保险科技": "20%",
                    "财富管理": "20%",
                },
                "entry_barrier": "中高（牌照 / 合规 / 信任）",
                "ai_company_accessible": {
                    "accessible": True,
                    "reason": "合规自动化 / 金融教育内容 / 数据服务环节可切入",
                },
                "opportunity_points": [
                    "合规文档自动化工具",
                    "金融产品对比与教育内容",
                    "支付数据聚合分析服务",
                ],
                "risks": "监管风险 / 牌照门槛 / 信任成本",
                "data_sources": [
                    "https://www.statista.com/outlook/digital-assets/fintech",
                    "https://www.mckinsey.com/industries/financial-services/our-insights",
                ],
            },
            {
                "industry_name": "网络安全（零信任 / SOC 服务 / 合规自动化）",
                "profit_scale": "$200B+（2026 全球网络安全市场）",
                "profit_margin": "60-80%（SaaS） / 40-60%（服务）",
                "growth_rate": "15-25% YoY",
                "profit_pool_distribution": {
                    "安全 SaaS": "40%",
                    "SOC 服务": "25%",
                    "合规自动化": "20%",
                    "咨询": "15%",
                },
                "entry_barrier": "中（技术 / 信任 / 认证）",
                "ai_company_accessible": {
                    "accessible": True,
                    "reason": "合规自动化 / 威胁情报内容 / 安全工具环节可切入",
                },
                "opportunity_points": [
                    "合规检查清单自动化工具",
                    "安全工具对比与测评内容",
                    "威胁情报聚合订阅服务",
                ],
                "risks": "技术门槛 / 信任成本 / 责任风险",
                "data_sources": [
                    "https://www.statista.com/outlook/it-services/cybersecurity",
                    "https://www.bcg.com/industries/technology-industry",
                ],
            },
            {
                "industry_name": "医疗健康生物科技（GLP-1 / 基因治疗 / 数字疗法）",
                "profit_scale": "$1.5T+（2026 全球医疗市场）",
                "profit_margin": "20-40%（制药） / 60-80%（数字疗法）",
                "growth_rate": "10-20% YoY",
                "profit_pool_distribution": {
                    "制药": "45%",
                    "数字疗法": "20%",
                    "医疗器械": "20%",
                    "服务": "15%",
                },
                "entry_barrier": "高（牌照 / 临床 / 监管）",
                "ai_company_accessible": {
                    "accessible": True,
                    "reason": "数字疗法 / 患者教育 / 数据聚合环节可切入，"
                    "核心制药环节不可切入",
                },
                "opportunity_points": [
                    "患者教育内容平台",
                    "临床试验数据聚合服务",
                    "数字疗法辅助工具",
                ],
                "risks": "监管风险 / 临床周期长 / 数据隐私",
                "data_sources": [
                    "https://www.statista.com/outlook/health/pharmaceuticals",
                    "https://www.mckinsey.com/industries/healthcare/our-insights",
                ],
            },
            {
                "industry_name": "加密货币与 Web3（交易所 / MEV / 流动性质押 / RWA）",
                "profit_scale": "$50-100B（年利润，周期性）",
                "profit_margin": "50-80%（交易所）",
                "growth_rate": "30-50% YoY（周期性）",
                "profit_pool_distribution": {
                    "交易所": "35%",
                    "流动性质押": "25%",
                    "MEV": "20%",
                    "RWA": "20%",
                },
                "entry_barrier": "中高（合规 / 技术 / 信任）",
                "ai_company_accessible": {
                    "accessible": True,
                    "reason": "数据服务 / 教育内容 / 工具环节可切入，"
                    "核心交易所环节不可切入",
                },
                "opportunity_points": [
                    "链上数据聚合与监控工具",
                    "Web3 项目教育内容平台",
                    "空投追踪与策略工具",
                ],
                "risks": "监管风险 / 周期性强 / 安全风险",
                "data_sources": [
                    "https://www.statista.com/outlook/digital-assets/cryptocurrencies",
                    "https://www.mckinsey.com/industries/financial-services/our-insights/the-institutional-investors-guide-to-blockchain-and-cryptoassets",
                ],
            },
            {
                "industry_name": "绿色能源与储能（光伏 / 电池 / 碳信用）",
                "profit_scale": "$600B+（2026 全球清洁能源市场）",
                "profit_margin": "15-30%（制造） / 40-60%（服务）",
                "growth_rate": "20-30% YoY",
                "profit_pool_distribution": {
                    "光伏": "35%",
                    "储能电池": "30%",
                    "碳信用": "20%",
                    "服务": "15%",
                },
                "entry_barrier": "高（资本 / 技术 / 政策）",
                "ai_company_accessible": {
                    "accessible": True,
                    "reason": "碳信用数据服务 / ROI 计算工具 / 内容环节可切入",
                },
                "opportunity_points": [
                    "碳信用价格聚合与监控服务",
                    "光伏 ROI 计算器与内容",
                    "储能项目数据聚合平台",
                ],
                "risks": "政策依赖 / 资本密集 / 技术迭代",
                "data_sources": [
                    "https://www.statista.com/outlook/energy",
                    "https://www.bcg.com/industries/energy-industry",
                ],
            },
        ]

    @staticmethod
    def _get_curated_value_chain_entries() -> List[Dict[str, Any]]:
        """返回最挣钱行业价值链切入点基线数据集。

        每个行业 3 个切入点，覆盖至少 3 种 entry_type
        （efficiency_tool / content_support / data_service / automation /
        marketing_support）。所有切入点 profit_pool_position 均为
        high-profit-chain（切入最挣钱行业价值链）。
        """
        return [
            # —— AI 应用层 ——
            {
                "industry": "AI 应用层（垂直 SaaS / Agent 平台 / Coding 助手）",
                "chain_segment": "垂直工具环节",
                "entry_type": "efficiency_tool",
                "description": "面向垂直行业的 AI 文档自动化工具（法律合同审查 / 财税报表生成）",
                "target_customer": "中小律所 / 财税事务所 / 企业法务部门",
                "value_proposition": "将文档处理时间从小时级降至分钟级，按使用量付费",
                "barrier_analysis": "需垂直行业 know-how + LLM 微调，随便一个人用通用 AI 做不出可靠工具",
                "startup_cost": "低（1-2 周 MVP，复用现有 LLM 能力）",
                "time_to_revenue": "7-14 天（首批种子客户）",
                "sustainability": "asset",
                "resource_match": "高（复用 LLM + 浏览器自动化能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            {
                "industry": "AI 应用层（垂直 SaaS / Agent 平台 / Coding 助手）",
                "chain_segment": "内容分发环节",
                "entry_type": "content_support",
                "description": "AI 工具对比测评站 + 教程内容，SEO 获客后导流至工具",
                "target_customer": "AI 工具采购方 / 开发者 / 企业 IT",
                "value_proposition": "提供中立对比 + 实测教程，降低选型成本",
                "barrier_analysis": "需持续实测 + 数据库积累，单次 AI 生成无法替代",
                "startup_cost": "低（3 天建站，持续运营）",
                "time_to_revenue": "14-30 天（affiliate + 广告）",
                "sustainability": "asset",
                "resource_match": "高（复用内容生成 + SEO 能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            {
                "industry": "AI 应用层（垂直 SaaS / Agent 平台 / Coding 助手）",
                "chain_segment": "营销环节",
                "entry_type": "marketing_support",
                "description": "AI 产品冷启动营销自动化（社媒矩阵 + 内容分发）",
                "target_customer": "AI 初创公司 / 独立开发者",
                "value_proposition": "一次配置持续产出多平台内容，降低获客成本",
                "barrier_analysis": "需多平台 API 集成 + 内容质量把控，工具化后有壁垒",
                "startup_cost": "低（1 周集成）",
                "time_to_revenue": "7-14 天",
                "sustainability": "service",
                "resource_match": "高（复用内容 + 自动化能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            # —— 企业服务 SaaS ——
            {
                "industry": "企业服务 SaaS（垂直行业 SaaS / 开发者工具）",
                "chain_segment": "选型环节",
                "entry_type": "data_service",
                "description": "SaaS 工具对比与选型数据平台（价格 / 功能 / 集成度）",
                "target_customer": "企业 IT 采购 / 创业团队",
                "value_proposition": "聚合公开数据 + 实测对比，降低选型决策成本",
                "barrier_analysis": "需持续维护数据库 + 实测，数据积累形成壁垒",
                "startup_cost": "低（3 天 MVP）",
                "time_to_revenue": "14-30 天（affiliate + 订阅）",
                "sustainability": "asset",
                "resource_match": "高（复用数据抓取 + 聚合能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            {
                "industry": "企业服务 SaaS（垂直行业 SaaS / 开发者工具）",
                "chain_segment": "集成环节",
                "entry_type": "automation",
                "description": "SaaS 工作流自动化模板（Zapier/Make 模板市场）",
                "target_customer": "运营团队 / 中小企业",
                "value_proposition": "即用型自动化模板，省去配置时间",
                "barrier_analysis": "需深入理解业务流程 + 持续维护模板兼容性",
                "startup_cost": "低（1-2 周首批模板）",
                "time_to_revenue": "14-30 天",
                "sustainability": "asset",
                "resource_match": "高（复用自动化能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            {
                "industry": "企业服务 SaaS（垂直行业 SaaS / 开发者工具）",
                "chain_segment": "内容环节",
                "entry_type": "content_support",
                "description": "SaaS 集成教程与最佳实践内容站",
                "target_customer": "SaaS 用户 / 运营团队",
                "value_proposition": "提供深度集成教程，解决官方文档不足的痛点",
                "barrier_analysis": "需实测 + 持续更新，单次 AI 生成无法覆盖边缘场景",
                "startup_cost": "低（3 天建站）",
                "time_to_revenue": "14-30 天",
                "sustainability": "asset",
                "resource_match": "高（复用内容能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            # —— 金融科技 ——
            {
                "industry": "金融科技（支付 / 嵌入式金融 / 保险科技）",
                "chain_segment": "合规环节",
                "entry_type": "efficiency_tool",
                "description": "合规文档自动化生成工具（KYC / AML 模板）",
                "target_customer": "金融科技初创公司 / 合规团队",
                "value_proposition": "将合规文档准备时间从天级降至小时级",
                "barrier_analysis": "需金融合规 know-how + 持续跟踪法规变化",
                "startup_cost": "中（1-2 月 MVP，需合规知识库）",
                "time_to_revenue": "30-60 天",
                "sustainability": "asset",
                "resource_match": "中（需补充合规领域知识）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            {
                "industry": "金融科技（支付 / 嵌入式金融 / 保险科技）",
                "chain_segment": "教育环节",
                "entry_type": "content_support",
                "description": "金融产品对比与教育内容平台",
                "target_customer": "个人投资者 / 小微企业主",
                "value_proposition": "中立对比 + 教育内容，降低金融决策门槛",
                "barrier_analysis": "需持续跟踪产品变化 + 数据准确性保障",
                "startup_cost": "低（1 周建站）",
                "time_to_revenue": "14-30 天（affiliate）",
                "sustainability": "asset",
                "resource_match": "高（复用内容能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            {
                "industry": "金融科技（支付 / 嵌入式金融 / 保险科技）",
                "chain_segment": "数据环节",
                "entry_type": "data_service",
                "description": "支付费率与通道数据聚合 API",
                "target_customer": "电商 / SaaS 平台 / 支付集成商",
                "value_proposition": "一次接入比价多家支付通道，降低集成成本",
                "barrier_analysis": "需持续抓取 + 数据准确性 + API 稳定性",
                "startup_cost": "中（2-3 周数据管道）",
                "time_to_revenue": "30-60 天（API 订阅）",
                "sustainability": "asset",
                "resource_match": "高（复用数据抓取能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            # —— 网络安全 ——
            {
                "industry": "网络安全（零信任 / SOC 服务 / 合规自动化）",
                "chain_segment": "合规环节",
                "entry_type": "automation",
                "description": "合规检查清单自动化工具（SOC2 / ISO27001）",
                "target_customer": "SaaS 公司 / 企业安全团队",
                "value_proposition": "自动生成合规证据 + 持续监控，降低审计成本",
                "barrier_analysis": "需深入理解合规框架 + 工具集成深度",
                "startup_cost": "中（1-2 月 MVP）",
                "time_to_revenue": "30-60 天",
                "sustainability": "asset",
                "resource_match": "中（需补充安全合规知识）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            {
                "industry": "网络安全（零信任 / SOC 服务 / 合规自动化）",
                "chain_segment": "内容环节",
                "entry_type": "content_support",
                "description": "安全工具对比与测评内容站",
                "target_customer": "企业安全采购 / CISO",
                "value_proposition": "提供中立实测对比，降低选型成本",
                "barrier_analysis": "需实测环境 + 持续跟踪漏洞情报",
                "startup_cost": "中（需测试环境）",
                "time_to_revenue": "30-60 天",
                "sustainability": "asset",
                "resource_match": "中（需安全测试能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            {
                "industry": "网络安全（零信任 / SOC 服务 / 合规自动化）",
                "chain_segment": "数据环节",
                "entry_type": "data_service",
                "description": "威胁情报聚合订阅服务",
                "target_customer": "安全运营团队 / MSSP",
                "value_proposition": "多源情报聚合 + 去重 + 优先级排序",
                "barrier_analysis": "需多数据源集成 + 数据质量保障",
                "startup_cost": "中（2-3 周数据管道）",
                "time_to_revenue": "30-60 天（订阅）",
                "sustainability": "asset",
                "resource_match": "高（复用数据聚合能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            # —— 医疗健康生物科技 ——
            {
                "industry": "医疗健康生物科技（GLP-1 / 基因治疗 / 数字疗法）",
                "chain_segment": "教育环节",
                "entry_type": "content_support",
                "description": "患者教育内容平台（疾病科普 + 治疗方案对比）",
                "target_customer": "患者 / 健康管理机构 / 医生",
                "value_proposition": "提供循证医学教育内容，降低医患沟通成本",
                "barrier_analysis": "需医学审校 + 内容准确性保障，不能纯 AI 生成",
                "startup_cost": "中（需医学顾问）",
                "time_to_revenue": "30-60 天",
                "sustainability": "asset",
                "resource_match": "中（需医学领域知识）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            {
                "industry": "医疗健康生物科技（GLP-1 / 基因治疗 / 数字疗法）",
                "chain_segment": "数据环节",
                "entry_type": "data_service",
                "description": "临床试验数据聚合服务",
                "target_customer": "药企 / 研究机构 / 投资机构",
                "value_proposition": "聚合公开临床试验数据 + 检索 + 分析",
                "barrier_analysis": "需理解临床数据结构 + 持续抓取 ClinicalTrials.gov",
                "startup_cost": "中（2-3 周数据管道）",
                "time_to_revenue": "30-60 天（订阅）",
                "sustainability": "asset",
                "resource_match": "高（复用数据抓取能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            {
                "industry": "医疗健康生物科技（GLP-1 / 基因治疗 / 数字疗法）",
                "chain_segment": "工具环节",
                "entry_type": "efficiency_tool",
                "description": "数字疗法辅助工具（症状追踪 + 用药提醒）",
                "target_customer": "数字疗法公司 / 患者",
                "value_proposition": "提升患者依从性，增强数字疗法效果",
                "barrier_analysis": "需医疗合规 + 数据隐私保障",
                "startup_cost": "中（1-2 月 MVP）",
                "time_to_revenue": "60-90 天",
                "sustainability": "asset",
                "resource_match": "中（需医疗合规知识）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            # —— 加密货币与 Web3 ——
            {
                "industry": "加密货币与 Web3（交易所 / MEV / 流动性质押 / RWA）",
                "chain_segment": "数据环节",
                "entry_type": "data_service",
                "description": "链上数据聚合与监控工具（巨鲸追踪 / 异常报警）",
                "target_customer": "加密交易员 / 投资机构 / DeFi 用户",
                "value_proposition": "实时链上数据聚合 + 智能报警，降低信息不对称",
                "barrier_analysis": "需链上数据索引能力 + 算法积累",
                "startup_cost": "中（2-3 周数据管道）",
                "time_to_revenue": "14-30 天（订阅）",
                "sustainability": "asset",
                "resource_match": "高（复用数据抓取能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            {
                "industry": "加密货币与 Web3（交易所 / MEV / 流动性质押 / RWA）",
                "chain_segment": "教育环节",
                "entry_type": "content_support",
                "description": "Web3 项目教育内容平台（项目解读 / 空投教程）",
                "target_customer": "Web3 新手 / 空投猎人",
                "value_proposition": "提供深度项目解析 + 实操教程，降低参与门槛",
                "barrier_analysis": "需持续跟踪项目动态 + 实操验证，不能纯 AI 生成",
                "startup_cost": "低（1 周建站）",
                "time_to_revenue": "7-14 天（affiliate + 广告）",
                "sustainability": "asset",
                "resource_match": "高（复用内容能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            {
                "industry": "加密货币与 Web3（交易所 / MEV / 流动性质押 / RWA）",
                "chain_segment": "工具环节",
                "entry_type": "efficiency_tool",
                "description": "空投追踪与策略工具",
                "target_customer": "空投猎人 / 加密投资者",
                "value_proposition": "聚合空投机会 + 自动化任务追踪，提升参与效率",
                "barrier_analysis": "需持续抓取多源数据 + 任务自动化集成",
                "startup_cost": "中（2-3 周 MVP）",
                "time_to_revenue": "14-30 天（订阅）",
                "sustainability": "asset",
                "resource_match": "高（复用抓取 + 自动化能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            # —— 绿色能源与储能 ——
            {
                "industry": "绿色能源与储能（光伏 / 电池 / 碳信用）",
                "chain_segment": "数据环节",
                "entry_type": "data_service",
                "description": "碳信用价格聚合与监控服务",
                "target_customer": "碳交易机构 / 企业 ESG 团队 / 投资机构",
                "value_proposition": "聚合多市场碳信用价格 + 趋势分析",
                "barrier_analysis": "需多市场数据源集成 + 数据准确性",
                "startup_cost": "中（2-3 周数据管道）",
                "time_to_revenue": "30-60 天（订阅）",
                "sustainability": "asset",
                "resource_match": "高（复用数据抓取能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            {
                "industry": "绿色能源与储能（光伏 / 电池 / 碳信用）",
                "chain_segment": "工具环节",
                "entry_type": "efficiency_tool",
                "description": "光伏 ROI 计算器与对比工具",
                "target_customer": "家庭 / 企业光伏采购方 / 安装商",
                "value_proposition": "基于实时电价与补贴数据计算投资回报",
                "barrier_analysis": "需实时电价 + 补贴政策数据集成",
                "startup_cost": "低（1-2 周 MVP）",
                "time_to_revenue": "14-30 天（affiliate + 广告）",
                "sustainability": "asset",
                "resource_match": "高（复用数据 + 工具能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            {
                "industry": "绿色能源与储能（光伏 / 电池 / 碳信用）",
                "chain_segment": "内容环节",
                "entry_type": "content_support",
                "description": "储能项目数据聚合与行业内容平台",
                "target_customer": "能源行业从业者 / 投资机构",
                "value_proposition": "提供项目数据库 + 行业深度内容",
                "barrier_analysis": "需持续跟踪项目 + 数据积累",
                "startup_cost": "中（2-3 周建站）",
                "time_to_revenue": "30-60 天（订阅 + 广告）",
                "sustainability": "asset",
                "resource_match": "高（复用内容 + 数据能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            # —— AI 基础设施与算力 ——
            {
                "industry": "AI 基础设施与算力（GPU 云 / 推理服务 / 模型托管）",
                "chain_segment": "工具环节",
                "entry_type": "efficiency_tool",
                "description": "GPU 算力价格聚合与比价工具",
                "target_customer": "AI 研究者 / 创业团队 / 模型工程师",
                "value_proposition": "一次查询比价多家 GPU 云，降低算力采购成本",
                "barrier_analysis": "需持续抓取多云价格 + 数据准确性",
                "startup_cost": "低（1-2 周 MVP）",
                "time_to_revenue": "14-30 天（affiliate + 订阅）",
                "sustainability": "asset",
                "resource_match": "高（复用数据抓取能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            {
                "industry": "AI 基础设施与算力（GPU 云 / 推理服务 / 模型托管）",
                "chain_segment": "监控环节",
                "entry_type": "data_service",
                "description": "模型推理成本监控仪表板",
                "target_customer": "AI 应用团队 / 平台工程",
                "value_proposition": "实时监控推理成本 + 异常报警，优化算力支出",
                "barrier_analysis": "需多平台 API 集成 + 成本归因算法",
                "startup_cost": "中（2-3 周 MVP）",
                "time_to_revenue": "30-60 天（订阅）",
                "sustainability": "asset",
                "resource_match": "高（复用数据 + 监控能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
            {
                "industry": "AI 基础设施与算力（GPU 云 / 推理服务 / 模型托管）",
                "chain_segment": "内容环节",
                "entry_type": "content_support",
                "description": "AI 基础设施教程与对比内容站",
                "target_customer": "AI 工程师 / 技术决策者",
                "value_proposition": "提供深度基础设施对比 + 部署教程",
                "barrier_analysis": "需实测 + 持续跟踪技术迭代",
                "startup_cost": "低（1 周建站）",
                "time_to_revenue": "14-30 天（affiliate + 广告）",
                "sustainability": "asset",
                "resource_match": "高（复用内容能力）",
                "profit_pool_position": _PROFIT_POOL_HIGH,
            },
        ]

    def generate_report(self) -> str:
        """产出 markdown 报告到 `company/knowledge/opportunities/realtime-scan-YYYY-MM-DD.md`。

        若 scan_all() 尚未调用，则自动调用一次。报告必须包含：验证时间戳、
        数据源 URL、当前状态、预期收益、启动门槛；失败平台标注"无法验证"。

        Returns:
            报告文件的绝对路径字符串。
        """
        # 若未扫描过则自动扫描
        if not self._last_scan:
            self.scan_all()

        today = datetime.date.today().isoformat()
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        report_path = self.output_dir / f"realtime-scan-{today}.md"

        # 统计
        total = len(self._last_scan)
        accessible_count = sum(1 for r in self._last_scan if r.get("accessible"))
        unverified_count = sum(1 for r in self._last_scan if r.get("status") == "unverified")
        # 行业利润池定位统计
        high_count = sum(
            1 for r in self._last_scan
            if r.get("industry_profit_pool_position") == _PROFIT_POOL_HIGH
        )
        mid_count = sum(
            1 for r in self._last_scan
            if r.get("industry_profit_pool_position") == _PROFIT_POOL_MID
        )
        low_count = sum(
            1 for r in self._last_scan
            if r.get("industry_profit_pool_position") == _PROFIT_POOL_LOW
        )

        lines: List[str] = [
            f"# 实时机会扫描报告 - {today}",
            "",
            f"**验证时间戳**：{timestamp}",
            f"**扫描平台数**：{total}",
            f"**可访问**：{accessible_count} / {total}",
            f"**无法验证**：{unverified_count} / {total}",
            f"**行业利润池定位**：high-profit-chain {high_count} / "
            f"mid {mid_count} / low-red-ocean {low_count}",
            "",
            "## 平台状态总览",
            "",
            "| 平台 | 当前状态 | 行业利润池定位 | 状态码 | 抓取耗时(s) | 数据源 URL |",
            "|------|----------|----------------|--------|-------------|-----------|",
        ]

        for r in self._last_scan:
            status_label = self._status_label(r)
            pool_label = self._profit_pool_label(r)
            lines.append(
                f"| {r.get('platform', '')} "
                f"| {status_label} "
                f"| {pool_label} "
                f"| {r.get('status_code', 0)} "
                f"| {r.get('fetch_time', 0)} "
                f"| {r.get('url', '')} |"
            )

        # 详细信息表（含预期收益 + 启动门槛 + 利润池定位）
        lines.extend([
            "",
            "## 平台详细信息",
            "",
            "| 平台 | 当前状态 | 行业利润池定位 | 预期收益 | 启动门槛 | 错误信息 |",
            "|------|----------|----------------|----------|----------|----------|",
        ])
        for r in self._last_scan:
            status_label = self._status_label(r)
            pool_label = self._profit_pool_label(r)
            err = r.get("error", "") or "—"
            lines.append(
                f"| {r.get('platform', '')} "
                f"| {status_label} "
                f"| {pool_label} "
                f"| {r.get('expected_reward', '')} "
                f"| {r.get('entry_barrier', '')} "
                f"| {err} |"
            )

        # 机会数说明
        lines.extend([
            "",
            "## 机会数量说明",
            "",
            "本扫描器仅验证平台 URL 当日可访问性，不实时解析页面机会数量。",
            "原因：多数平台为 SPA 渲染，静态抓取无法可靠解析机会数；",
            "为遵守诚实原则，避免编造，统一标注为「未解析」。",
            "机会数详情请参考 `radar-YYYY-MM-DD.md`（机会雷达报告）。",
            "",
        ])

        # 行业利润池定位说明
        lines.extend([
            "## 行业利润池定位说明",
            "",
            "本报告按「是否切入最挣钱行业」优先排序，定位分三档：",
            "- **high-profit-chain**：切入最挣钱行业价值链（排最前）",
            "- **mid**：中等利润行业",
            "- **low-red-ocean**：低附加值红海（排最后）",
            "",
        ])

        # 价值链切入点清单（high-profit-chain）
        value_chain_items = [
            r for r in self._last_scan
            if r.get("track_category") == "value-chain-entry"
        ]
        if value_chain_items:
            lines.extend([
                "## 最挣钱行业价值链切入点",
                "",
                "以下为切入最挣钱行业价值链的机会点（high-profit-chain，已排最前）：",
                "",
                "| 所属行业 | 价值链环节 | 切入点类型 | 描述 | 目标客户 | 到账速度 | 可持续性 |",
                "|----------|------------|------------|------|----------|----------|----------|",
            ])
            for r in value_chain_items:
                lines.append(
                    f"| {r.get('industry', '')} "
                    f"| {r.get('chain_segment', '')} "
                    f"| {r.get('entry_type', '')} "
                    f"| {r.get('description', '')} "
                    f"| {r.get('target_customer', '')} "
                    f"| {r.get('time_to_revenue', '')} "
                    f"| {r.get('sustainability', '')} |"
                )
            lines.append("")

        # 失败平台清单
        failed = [r for r in self._last_scan if not r.get("accessible")]
        if failed:
            lines.extend([
                "## 无法验证的平台",
                "",
                "以下平台当日抓取失败，标注为「无法验证」，需人工复核：",
                "",
            ])
            for r in failed:
                lines.append(
                    f"- **{r.get('platform', '')}** ({r.get('url', '')}) "
                    f"— 错误：{r.get('error', '未知')}"
                )
            lines.append("")

        # 数据源 URL 汇总
        lines.extend([
            "## 数据源 URL 汇总",
            "",
        ])
        for r in self._last_scan:
            lines.append(f"- {r.get('platform', '')}: {r.get('url', '')}")

        lines.extend([
            "",
            "## 说明",
            "- 报告由 `RealtimeOpportunityScanner` 自动生成，使用 Python 标准库 urllib。",
            "- 单个平台失败不影响其他平台扫描（独立 try/except）。",
            "- 「无法验证」表示网络抓取失败（超时 / 连接错误 / HTTP 错误），",
            "  不代表平台本身不可用，建议人工访问确认。",
        ])

        content = "\n".join(lines)
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            report_path.write_text(content, encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            logger.error("报告写入失败 %s: %s", report_path, e)
            raise

        return str(report_path)

    # ------------------------------------------------------------------
    # 私有辅助
    # ------------------------------------------------------------------

    @staticmethod
    def _status_label(record: Dict[str, Any]) -> str:
        """根据扫描记录返回中文状态标签。"""
        status = record.get("status", "")
        if status == "accessible":
            return "✅ 可访问"
        if status == "inaccessible":
            return "❌ 不可访问"
        if status == "opportunity":
            return "💡 机会点"
        if status == "timeout":
            return "⏱️ 超时"
        if status == "error":
            return "⚠️ 错误"
        return "⚠️ 无法验证"

    @staticmethod
    def _profit_pool_label(record: Dict[str, Any]) -> str:
        """根据扫描记录返回行业利润池定位中文标签。"""
        position = record.get("industry_profit_pool_position", _PROFIT_POOL_MID)
        if position == _PROFIT_POOL_HIGH:
            return "🔥 high-profit-chain"
        if position == _PROFIT_POOL_MID:
            return "⚪ mid"
        return "🧊 low-red-ocean"


if __name__ == "__main__":
    # 直接运行本模块时执行一次扫描并打印结果
    logging.basicConfig(level=logging.INFO)
    scanner = RealtimeOpportunityScanner()
    scan_results = scanner.scan_all()
    path = scanner.generate_report()
    print(f"\n报告已生成：{path}")
    for r in scan_results:
        print(
            f"  - {r['platform']}: {r['status']} "
            f"(HTTP {r['status_code']}, {r['fetch_time']}s)"
        )
