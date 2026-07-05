"""订阅额度管理器

管理付费用户的订阅状态与文章生成额度。
数据存储在 data/subscriptions.json（本地文件，沙盒模式适用）。

订阅状态流转：
    - active：有效订阅，可扣减额度
    - expired：到期自动标记（当前时间 > expires_at）
    - cancelled：同 email 新增订阅时，旧 active 订阅标记为 cancelled

数据结构（data/subscriptions.json）:
    {
        "subscriptions": [
            {
                "email": "user@example.com",
                "plan_id": "STARTER_MONTHLY",
                "subscription_id": "sub_xxx",
                "quota": 50,
                "used": 3,
                "status": "active",
                "started_at": "2026-06-27T08:00:00",
                "expires_at": "2026-07-27T08:00:00",
                "created_at": "2026-06-27T08:00:00"
            }
        ]
    }
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Optional


# 订阅计划定义（与 PayPalClient.SUBSCRIPTION_PLANS 对应）
SUBSCRIPTION_PLANS = {
    "STARTER_MONTHLY": {
        "name": "Starter Monthly",
        "price": 29.00,
        "currency": "USD",
        "quota": 50,  # 每月 50 篇
        "duration_days": 30,
    },
    "PRO_MONTHLY": {
        "name": "Pro Monthly",
        "price": 79.00,
        "currency": "USD",
        "quota": 200,
        "duration_days": 30,
    },
    "ARTICLE_SINGLE": {
        "name": "Single Article",
        "price": 2.00,
        "currency": "USD",
        "quota": 1,
        "duration_days": 365,  # 单篇长期有效
    },
}


class SubscriptionManager:
    """订阅额度管理器

    负责订阅记录的增删查改与额度扣减。所有数据持久化到本地 JSON 文件，
    适用于沙盒模式与单机部署。

    使用示例：
        >>> mgr = SubscriptionManager()
        >>> mgr.add_subscription("user@example.com", "STARTER_MONTHLY", "sub_xxx")
        >>> mgr.check_quota("user@example.com")
        {'quota': 50, 'used': 0, 'remaining': 50, ...}
        >>> mgr.consume_quota("user@example.com")
        {'success': True, 'remaining': 49, 'message': '...'}
    """

    def __init__(self, data_dir: str = None):
        """初始化

        Args:
            data_dir: 数据目录路径，默认为项目根的 data/
        """
        # 默认 data_dir 为本文件上级目录的 data/
        if data_dir is None:
            data_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "data"
            )
        self.data_dir = data_dir
        self.data_file = os.path.join(data_dir, "subscriptions.json")
        self._ensure_data_file()

    # --------------------------------------------------------------------------
    # 内部工具：文件读写与状态刷新
    # --------------------------------------------------------------------------

    def _ensure_data_file(self):
        """确保数据文件存在，不存在则创建空结构。"""
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.data_file):
            self._write({"subscriptions": []})

    def _read(self) -> dict:
        """读取数据"""
        with open(self.data_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: dict):
        """写入数据"""
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _refresh_status(self):
        """刷新过期状态：到期订阅标记为 expired

        遍历所有 active 订阅，若当前时间 > expires_at，则改为 expired。
        只在状态发生变化时回写文件，避免无谓 IO。
        """
        data = self._read()
        now = datetime.now()
        changed = False
        for sub in data.get("subscriptions", []):
            if sub.get("status") != "active":
                continue
            expires_at = sub.get("expires_at")
            if not expires_at:
                continue
            try:
                expire_dt = datetime.fromisoformat(expires_at)
            except (ValueError, TypeError):
                continue
            if now > expire_dt:
                sub["status"] = "expired"
                changed = True
        if changed:
            self._write(data)

    def _find_active(self, subscriptions: list, email: str) -> Optional[dict]:
        """从列表中查找指定 email 的 active 订阅（返回引用，便于原地修改）。"""
        for sub in subscriptions:
            if sub.get("email") == email and sub.get("status") == "active":
                return sub
        return None

    # --------------------------------------------------------------------------
    # 公开 API
    # --------------------------------------------------------------------------

    def add_subscription(
        self, email: str, plan_id: str, subscription_id: str
    ) -> dict:
        """新增订阅

        同 email 的旧 active 订阅标记为 cancelled，新增一条 active 订阅。
        quota 与 duration_days 从 SUBSCRIPTION_PLANS 读取。

        Args:
            email: 用户邮箱
            plan_id: 计划 ID（STARTER_MONTHLY / PRO_MONTHLY / ARTICLE_SINGLE）
            subscription_id: PayPal 订阅 ID 或订单 ID

        Returns:
            新增的订阅记录

        Raises:
            ValueError: plan_id 未知时抛出
        """
        if plan_id not in SUBSCRIPTION_PLANS:
            raise ValueError(
                f"未知订阅计划 plan_id={plan_id}，"
                f"可选：{list(SUBSCRIPTION_PLANS.keys())}"
            )

        self._refresh_status()
        data = self._read()
        subscriptions = data.setdefault("subscriptions", [])

        # 同 email 旧 active 订阅标记为 cancelled
        for sub in subscriptions:
            if (
                sub.get("email") == email
                and sub.get("status") == "active"
            ):
                sub["status"] = "cancelled"

        plan = SUBSCRIPTION_PLANS[plan_id]
        now = datetime.now()
        started_at = now.replace(microsecond=0)
        expires_at = started_at + timedelta(days=plan["duration_days"])

        record = {
            "email": email,
            "plan_id": plan_id,
            "subscription_id": subscription_id,
            "quota": plan["quota"],
            "used": 0,
            "status": "active",
            "started_at": started_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "created_at": started_at.isoformat(),
        }
        subscriptions.append(record)
        self._write(data)
        return record

    def consume_quota(self, email: str) -> dict:
        """扣减额度

        找到 email 的 active 订阅，used += 1；额度耗尽时不扣减并返回 success=False。

        Args:
            email: 用户邮箱

        Returns:
            {success, remaining, message}

        Raises:
            ValueError: 用户无 active 订阅时抛出
        """
        self._refresh_status()
        data = self._read()
        subscriptions = data.get("subscriptions", [])
        sub = self._find_active(subscriptions, email)
        if sub is None:
            raise ValueError(
                f"用户 {email} 无有效订阅，无法扣减额度"
            )

        used = sub.get("used", 0)
        quota = sub.get("quota", 0)
        if used >= quota:
            return {
                "success": False,
                "remaining": 0,
                "message": f"额度已耗尽（{used}/{quota}），请续费",
            }

        sub["used"] = used + 1
        remaining = quota - sub["used"]
        self._write(data)
        return {
            "success": True,
            "remaining": remaining,
            "message": f"扣减成功，剩余 {remaining}/{quota}",
        }

    def check_quota(self, email: str) -> dict:
        """查询剩余额度

        Args:
            email: 用户邮箱

        Returns:
            {quota, used, remaining, plan_id, expires_at, status}
            无 active 订阅返回 {quota: 0, used: 0, remaining: 0, ...}
        """
        self._refresh_status()
        data = self._read()
        subscriptions = data.get("subscriptions", [])
        sub = self._find_active(subscriptions, email)
        if sub is None:
            return {
                "quota": 0,
                "used": 0,
                "remaining": 0,
                "plan_id": None,
                "expires_at": None,
                "status": None,
            }

        quota = sub.get("quota", 0)
        used = sub.get("used", 0)
        return {
            "quota": quota,
            "used": used,
            "remaining": max(quota - used, 0),
            "plan_id": sub.get("plan_id"),
            "expires_at": sub.get("expires_at"),
            "status": sub.get("status"),
        }

    def is_active(self, email: str) -> bool:
        """判断订阅是否有效（有 active 订阅且未过期）

        Args:
            email: 用户邮箱

        Returns:
            True 表示存在有效订阅可扣减额度
        """
        self._refresh_status()
        data = self._read()
        subscriptions = data.get("subscriptions", [])
        return self._find_active(subscriptions, email) is not None

    def list_subscriptions(self, email: str = None) -> list:
        """列出订阅（可按 email 过滤）

        Args:
            email: 可选，按 email 过滤；为 None 时返回全部

        Returns:
            订阅记录列表（按创建时间顺序）
        """
        self._refresh_status()
        data = self._read()
        subscriptions = data.get("subscriptions", [])
        if email is None:
            return list(subscriptions)
        return [s for s in subscriptions if s.get("email") == email]
