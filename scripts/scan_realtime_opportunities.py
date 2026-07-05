"""实时机会扫描器 CLI 入口

用法：
    python d:\\autoCompany\\scripts\\scan_realtime_opportunities.py

功能：
1. 调用 RealtimeOpportunityScanner.scan_all() 验证 5 个平台当日可访问性
2. 调用 generate_report() 产出 markdown 报告到
   company/knowledge/opportunities/realtime-scan-YYYY-MM-DD.md
3. 打印扫描进度与每个平台的状态
4. 输出报告文件绝对路径
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

# 让脚本能从项目根目录导入 engine 包（无论从哪里调用）
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from engine.crypto.realtime_opportunity_scanner import RealtimeOpportunityScanner  # noqa: E402


def main() -> int:
    """CLI 主入口。返回退出码（0 = 成功）。"""
    print("=" * 60)
    print("AutoCorp 实时机会扫描器")
    print(f"启动时间：{datetime.datetime.now().isoformat(timespec='seconds')}")
    print("=" * 60)

    scanner = RealtimeOpportunityScanner()

    # ---- 阶段 1：扫描所有平台 ----
    print(f"\n[1/2] 开始扫描 {len(scanner.targets)} 个平台...")
    for i, target in enumerate(scanner.targets, 1):
        print(f"  [{i}/{len(scanner.targets)}] 准备验证：{target['platform']} - {target['url']}")

    results = scanner.scan_all()

    # ---- 打印扫描进度与结果 ----
    print("\n扫描结果：")
    print("-" * 60)
    for r in results:
        status_label = _status_label(r)
        err = f" | 错误: {r['error']}" if r.get("error") else ""
        print(
            f"  {status_label}  {r['platform']:<18} "
            f"HTTP {r['status_code']:<3}  {r['fetch_time']}s{err}"
        )
    print("-" * 60)

    accessible = sum(1 for r in results if r.get("accessible"))
    unverified = sum(1 for r in results if r.get("status") == "unverified")
    print(
        f"汇总：可访问 {accessible}/{len(results)}，"
        f"无法验证 {unverified}/{len(results)}"
    )

    # ---- 阶段 2：生成报告 ----
    print("\n[2/2] 生成 markdown 报告...")
    try:
        report_path = scanner.generate_report()
    except Exception as e:  # noqa: BLE001
        print(f"[ERROR] 报告生成失败：{e}")
        return 1

    print(f"\n[OK] 报告已生成：{report_path}")
    print("=" * 60)
    return 0


def _status_label(record: dict) -> str:
    """返回中文状态标签，与报告内一致。"""
    status = record.get("status", "")
    if status == "accessible":
        return "[OK]   可访问"
    if status == "inaccessible":
        return "[FAIL] 不可访问"
    return "[WARN] 无法验证"


if __name__ == "__main__":
    sys.exit(main())
