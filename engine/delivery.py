"""标准化交付包打包器

提供 DeliveryPackager 类，负责为「自产产品」与「服务订单」产出标准化的交付包，
统一打包 README / PRD / 架构 / 源码 / 测试报告 / 推广方案 / 验收单 等文档，
并在交付前校验必填字段是否已填写（未填字段视为阻塞项）。

设计原则：
1. 模板驱动：所有文档必须基于 ``company/templates/`` 下对应模板产出，未填字段
   统一使用 ``[REQUIRED: 字段描述]`` 标记。
2. 文件即数据库：交付包以目录形式持久化，不引入压缩包或数据库。
3. 优雅降级：缺失文档自动用模板创建占位文件，不抛异常；校验时返回结构化结果。
4. 向后兼容：``output_dir`` 参数可选，为空时使用默认路径。

典型用法::

    from engine.delivery import DeliveryPackager

    packager = DeliveryPackager()

    # 为自产产品构建交付包
    result = packager.build_for_product("seo-content-generator")
    # result = {pack_path, files: [...], missing_files: [...]}

    # 为服务订单构建交付包
    result = packager.build_for_order("ord-20260629-001")

    # 校验交付包是否填写完整
    report = packager.validate(result["pack_path"], pack_type="product")
    # report = {valid: bool, missing_files: [...], unfilled_fields: [...]}
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from engine.workspace import WorkspaceManager


# 必填字段标记正则：匹配 [REQUIRED: 字段描述] 形式的标记
# 使用 lazy 匹配避免贪婪吞掉同一行后续内容；DOTALL 不开启以保持单行内匹配
_REQUIRED_FIELD_RE = re.compile(r"\[REQUIRED:\s*(.+?)\]")


# 自产产品交付包应包含的 6 项文档清单（相对 pack 根目录的路径）
# - 文件项：直接检查文件是否存在
# - 目录项（source/）：检查目录是否存在
PRODUCT_DOC_ITEMS: List[str] = [
    "README.md",
    "prd.md",
    "architecture.md",
    "source/",
    "test-report.md",
    "promotion-plan.md",
]

# 服务订单交付包应包含的 5 项文档清单
ORDER_DOC_ITEMS: List[str] = [
    "README.md",
    "prd.md",
    "source/",
    "test-report.md",
    "acceptance.md",
]

# 文档名 → 模板名 映射（用于缺失时创建占位文件）
# README 与 source/ 无对应模板，由 _placeholder_for 单独处理
_DOC_TO_TEMPLATE: dict[str, str] = {
    "prd.md": "prd",
    "architecture.md": "architecture",
    "test-report.md": "test-report",
    "promotion-plan.md": "promotion-plan",
    "acceptance.md": "acceptance",
}


class DeliveryPackager:
    """标准化交付包打包器。

    为自产产品（``company/projects/<product>/``）与服务订单
    （``company/orders/delivered/<order_id>/``）构建标准化交付包：

    - 自产产品：6 项文档（README / PRD / 架构 / source / 测试报告 / 推广方案）
    - 服务订单：5 项文档（README / PRD / source / 测试报告 / 验收单）

    缺失文档自动用 ``company/templates/`` 下对应模板创建占位文件（含
    ``[REQUIRED: ...]`` 标记），交付前调用 ``validate`` 校验必填字段是否已填。
    """

    def __init__(self, workspace: Optional[WorkspaceManager] = None) -> None:
        """初始化交付包打包器。

        Args:
            workspace: WorkspaceManager 实例。为 None 时使用默认工作区
                （``d:\\autoCompany\\company``）。模板目录固定为
                ``<workspace.root_dir>/templates/``，产品目录为
                ``<workspace.root_dir>/projects/``，订单交付目录为
                ``<workspace.root_dir>/orders/delivered/``。
        """
        self.workspace: WorkspaceManager = workspace or WorkspaceManager()
        # 模板目录：company/templates/
        self.templates_dir: Path = self.workspace.root_dir / "templates"
        # 自产产品目录：company/projects/
        self.projects_dir: Path = self.workspace.root_dir / "projects"
        # 订单交付目录：company/orders/delivered/
        self.orders_dir: Path = self.workspace.root_dir / "orders"
        self.delivered_dir: Path = self.orders_dir / "delivered"

    # ------------------------------------------------------------------
    # 模板加载
    # ------------------------------------------------------------------
    def load_template(self, template_name: str) -> str:
        """从 ``company/templates/`` 加载指定模板内容。

        模板名约定：``template_name`` 为不带 ``-template.md`` 后缀的短名，
        如 ``"prd"`` 对应 ``prd-template.md``。也兼容直接传入完整文件名
        （如 ``"prd-template.md"``）或带 ``-template`` 后缀的短名
        （如 ``"prd-template"``）。

        Args:
            template_name: 模板名，如 ``"prd"`` / ``"architecture"`` /
                ``"test-report"`` / ``"promotion-plan"`` / ``"acceptance"``。

        Returns:
            模板文件文本内容（utf-8 解码）；模板不存在时返回空字符串。
        """
        # 规整 template_name 为完整文件名
        if template_name.endswith(".md"):
            filename = template_name
        elif template_name.endswith("-template"):
            filename = f"{template_name}.md"
        else:
            filename = f"{template_name}-template.md"

        path = self.templates_dir / filename
        if not path.exists():
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return ""

    # ------------------------------------------------------------------
    # 占位文件生成
    # ------------------------------------------------------------------
    def _placeholder_for(self, doc_name: str, subject: str) -> str:
        """为缺失文档生成占位内容。

        优先使用 ``company/templates/`` 下对应模板；若无对应模板
        （如 README.md / source/），生成一个最小化的占位内容，包含
        ``[REQUIRED: ...]`` 标记以阻塞交付校验，提示人工填写。

        Args:
            doc_name: 文档相对路径，如 ``"prd.md"`` / ``"README.md"``。
            subject: 主题名（产品名或订单 ID），用于占位标题。

        Returns:
            占位文件文本内容（含 ``[REQUIRED: ...]`` 标记）。
        """
        template_key = _DOC_TO_TEMPLATE.get(doc_name)
        if template_key:
            content = self.load_template(template_key)
            if content:
                return content

        # README.md 与 source/ 等无模板的项：生成最小化占位
        return (
            f"# {doc_name} - {subject}\n\n"
            f"> 本文件由 DeliveryPackager 自动创建占位，请人工填写。\n\n"
            f"[REQUIRED: {doc_name} 内容]\n"
        )

    # ------------------------------------------------------------------
    # 通用打包逻辑
    # ------------------------------------------------------------------
    def _build_pack(
        self,
        pack_path: Path,
        doc_items: List[str],
        subject: str,
    ) -> dict:
        """通用打包逻辑：检查并收集文档，缺失则用模板创建占位。

        Args:
            pack_path: 交付包根目录绝对路径。
            doc_items: 应包含的文档清单（相对 pack 根目录的路径列表）。
            subject: 主题名（产品名或订单 ID），用于占位标题与日志。

        Returns:
            ``{pack_path, files, missing_files}``：
                - ``pack_path``: 交付包根目录绝对路径（字符串形式）
                - ``files``: 已存在（含本次新建）的文档相对路径列表
                - ``missing_files``: 本次打包前缺失的文档相对路径列表
                  （已用占位文件补齐，仍需人工填写）
        """
        # 确保交付包根目录存在
        pack_path.mkdir(parents=True, exist_ok=True)

        files: List[str] = []
        missing_files: List[str] = []

        for item in doc_items:
            item_path = pack_path / item
            # 目录项（以 / 或 \\ 结尾）
            is_dir_item = item.endswith("/") or item.endswith("\\")
            if is_dir_item:
                if item_path.exists() and item_path.is_dir():
                    files.append(item)
                else:
                    # 创建目录占位
                    item_path.mkdir(parents=True, exist_ok=True)
                    # 在 source/ 下放一个占位文件，提示需要放入实际产出
                    placeholder_file = item_path / ".gitkeep"
                    placeholder_content = (
                        f"# {item} 占位目录 - {subject}\n\n"
                        f"> 本目录由 DeliveryPackager 自动创建，请放入实际交付内容。\n\n"
                        f"[REQUIRED: {item} 内容]\n"
                    )
                    try:
                        placeholder_file.write_text(
                            placeholder_content, encoding="utf-8"
                        )
                    except OSError as e:  # noqa: BLE001 - 写入失败优雅降级
                        print(f"[delivery] 创建占位文件失败 {placeholder_file}: {e}")
                    missing_files.append(item)
                    files.append(item)
            else:
                # 文件项
                if item_path.exists() and item_path.is_file():
                    files.append(item)
                else:
                    # 确保父目录存在
                    item_path.parent.mkdir(parents=True, exist_ok=True)
                    content = self._placeholder_for(item, subject)
                    try:
                        item_path.write_text(content, encoding="utf-8")
                    except OSError as e:  # noqa: BLE001 - 写入失败优雅降级
                        print(f"[delivery] 创建占位文件失败 {item_path}: {e}")
                    missing_files.append(item)
                    files.append(item)

        return {
            "pack_path": str(pack_path),
            "files": files,
            "missing_files": missing_files,
        }

    # ------------------------------------------------------------------
    # 公开 API - 构建交付包
    # ------------------------------------------------------------------
    def build_for_product(
        self,
        product_name: str,
        output_dir: Optional[Path] = None,
    ) -> dict:
        """为自产产品构建标准化交付包。

        在 ``company/projects/<product_name>/`` 下检查并收集 6 项文档：
        README.md / prd.md / architecture.md / source/ / test-report.md /
        promotion-plan.md。缺失文档使用模板创建占位文件（含
        ``[REQUIRED: ...]`` 标记）。

        Args:
            product_name: 产品名（即 ``company/projects/`` 下的子目录名）。
            output_dir: 自定义输出目录；为 None 时使用默认路径
                ``company/projects/<product_name>/``。

        Returns:
            ``{pack_path, files, missing_files}``：
                - ``pack_path``: 交付包根目录绝对路径（字符串形式）
                - ``files``: 已收集（含新建占位）的文档相对路径列表
                - ``missing_files``: 本次打包前缺失、已用占位补齐的文档
                  相对路径列表（仍需人工填写）
        """
        if output_dir is not None:
            pack_path = Path(output_dir).resolve()
        else:
            pack_path = self.projects_dir / product_name
        return self._build_pack(pack_path, PRODUCT_DOC_ITEMS, product_name)

    def build_for_order(
        self,
        order_id: str,
        output_dir: Optional[Path] = None,
    ) -> dict:
        """为服务订单构建标准化交付包。

        在 ``company/orders/delivered/<order_id>/`` 下检查并收集 5 项文档：
        README.md / prd.md / source/ / test-report.md / acceptance.md。
        缺失文档使用模板创建占位文件（含 ``[REQUIRED: ...]`` 标记）。

        Args:
            order_id: 订单 ID（如 ``ord-20260629-001``）。
            output_dir: 自定义输出目录；为 None 时使用默认路径
                ``company/orders/delivered/<order_id>/``。

        Returns:
            ``{pack_path, files, missing_files}``：
                - ``pack_path``: 交付包根目录绝对路径（字符串形式）
                - ``files``: 已收集（含新建占位）的文档相对路径列表
                - ``missing_files``: 本次打包前缺失、已用占位补齐的文档
                  相对路径列表（仍需人工填写）
        """
        if output_dir is not None:
            pack_path = Path(output_dir).resolve()
        else:
            pack_path = self.delivered_dir / order_id
        return self._build_pack(pack_path, ORDER_DOC_ITEMS, order_id)

    # ------------------------------------------------------------------
    # 校验
    # ------------------------------------------------------------------
    def _check_required_fields(self, file_path: Path) -> List[dict]:
        """扫描文件中 ``[REQUIRED: xxx]`` 标记，返回未填字段列表。

        使用正则匹配 ``[REQUIRED: 字段描述]`` 形式的标记，每个匹配项视为
        一个未填字段。``[可选: xxx]`` 等非必填标记不会被匹配。

        Args:
            file_path: 待扫描的文件绝对路径。

        Returns:
            未填字段字典列表，每项形如 ``{"field": "字段描述"}``。
            文件不存在或读取失败时返回空列表。
        """
        if not file_path.exists() or not file_path.is_file():
            return []
        try:
            text = file_path.read_text(encoding="utf-8")
        except OSError:
            return []
        matches = _REQUIRED_FIELD_RE.findall(text)
        # 去除字段描述首尾空白，保留原文本
        return [{"field": m.strip()} for m in matches if m.strip()]

    def validate(
        self,
        pack_path: Path,
        pack_type: str = "product",
    ) -> dict:
        """校验交付包必填字段是否填写完整。

        校验规则：
            1. 检查 ``pack_type`` 对应的所有文档是否存在（缺失加入
               ``missing_files``）
            2. 对每个已存在的文件项扫描 ``[REQUIRED: ...]`` 标记，
               未填字段加入 ``unfilled_fields``
            3. ``valid`` 为 True 当且仅当无缺失文件且无未填字段

        Args:
            pack_path: 交付包根目录路径（字符串或 Path 均可）。
            pack_type: 交付包类型，``"product"``（6 项文档）或
                ``"order"``（5 项文档）。其他值按 ``"product"`` 处理。

        Returns:
            ``{valid, missing_files, unfilled_fields}``：
                - ``valid``: 是否通过校验（bool）
                - ``missing_files``: 缺失文档相对路径列表
                - ``unfilled_fields``: 未填字段列表，每项
                  ``{file: 相对路径, field: 字段描述}``
        """
        pack_root = Path(pack_path).resolve()
        if pack_type == "order":
            doc_items = ORDER_DOC_ITEMS
        else:
            doc_items = PRODUCT_DOC_ITEMS

        missing_files: List[str] = []
        unfilled_fields: List[dict] = []

        for item in doc_items:
            item_path = pack_root / item
            is_dir_item = item.endswith("/") or item.endswith("\\")
            if is_dir_item:
                # 目录项：仅检查存在性
                if not (item_path.exists() and item_path.is_dir()):
                    missing_files.append(item)
                # 目录项不扫描必填字段（其内部占位文件不参与校验）
                continue

            # 文件项：检查存在性 + 扫描必填字段
            if not (item_path.exists() and item_path.is_file()):
                missing_files.append(item)
                continue

            unfilled = self._check_required_fields(item_path)
            for entry in unfilled:
                unfilled_fields.append({"file": item, "field": entry["field"]})

        valid = (len(missing_files) == 0) and (len(unfilled_fields) == 0)
        return {
            "valid": valid,
            "missing_files": missing_files,
            "unfilled_fields": unfilled_fields,
        }
