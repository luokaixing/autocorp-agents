"""AutoCorp 虚拟员工智能体集合

导出 7 个虚拟员工角色类：
    CEO / CTO / COO / Architect / Programmer / Tester / ProductManager

用法：
    from engine.agents import CEO, ProductManager
    ceo = CEO(workspace)
"""
from engine.agents.base import BaseAgent
from engine.agents.ceo import CEO
from engine.agents.cto import CTO
from engine.agents.coo import COO
from engine.agents.architect import Architect
from engine.agents.programmer import Programmer
from engine.agents.tester import Tester
from engine.agents.product_manager import ProductManager

__all__ = [
    "BaseAgent",
    "CEO",
    "CTO",
    "COO",
    "Architect",
    "Programmer",
    "Tester",
    "ProductManager",
]
